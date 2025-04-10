import os
import numpy as np
from django.conf import settings
from celery import shared_task
from .models import Video, EmotionAnalysis, EmotionAnalysisSummary
from .utils.emotion_detector import EmotionDetector

@shared_task
def analyze_video_emotions(video_id, frame_rate=1.0):
    """
    Process video and detect emotions in each frame
    Args:
        video_id: UUID of the video to process
        frame_rate: Number of frames per second to analyze
    """
    try:
        # Get video instance
        video = Video.objects.get(id=video_id)
        
        # Update status to processing
        video.status = 'processing'
        video.save()
        
        # Initialize emotion detector
        detector = EmotionDetector()
        video_path = os.path.join(settings.MEDIA_ROOT, video.file.name)
        
        # Analyze video
        results = detector.analyze_video(video_path, frame_rate)
        
        if not results:
            video.status = 'failed'
            video.save()
            print(f"No analysis results returned for video {video_id}")
            return False
            
        # Store individual frame results
        emotion_analyses = []
        
        # Define supported emotions for the new model
        supported_emotions = ['angry', 'sad', 'happy']
        
        # Initialize emotion sums dictionary with only supported emotions
        emotion_sums = {emotion: 0.0 for emotion in supported_emotions}
        
        # Process each frame result
        for result in results:
            timestamp = result['timestamp']
            
            # Verify all required emotions are present in the result
            for emotion in supported_emotions:
                if emotion not in result:
                    print(f"Missing emotion '{emotion}' in frame results. Got: {list(result.keys())}")
                    video.status = 'failed'
                    video.save()
                    return False
            
            # Create analysis object with only the emotions our model supports
            analysis_data = {
                'video': video,
                'timestamp': timestamp
            }
            
            # Add only the emotions from our new model
            for emotion in supported_emotions:
                analysis_data[emotion] = result[emotion]
                emotion_sums[emotion] += result[emotion]
            
            # Create EmotionAnalysis instance
            analysis = EmotionAnalysis(**analysis_data)
            emotion_analyses.append(analysis)
        
        # Bulk create all emotion analyses
        EmotionAnalysis.objects.bulk_create(emotion_analyses)
        
        # Calculate averages
        num_frames = len(results)
        emotion_avgs = {emotion: (emotion_sums[emotion] / num_frames) if num_frames > 0 else 0.0 
                       for emotion in emotion_sums}
        
        # Create summary object with only supported emotions
        summary_data = {'video': video}
        
        # Add averages for supported emotions only
        for emotion in supported_emotions:
            summary_data[f"{emotion}_avg"] = emotion_avgs[emotion]
            
        # For compatibility with database model, set other emotions to 0.0 if they exist in the model
        # This prevents database errors if your model still has these fields
        other_emotions = ['disgust', 'fear', 'neutral', 'surprised']
        for emotion in other_emotions:
            field_name = f"{emotion}_avg"
            # Check if the field exists in the model
            if hasattr(EmotionAnalysisSummary, field_name):
                summary_data[field_name] = 0.0
        
        # Create or update summary
        summary, created = EmotionAnalysisSummary.objects.update_or_create(
            video=video,
            defaults=summary_data
        )
        
        # Update video status to completed
        video.status = 'completed'
        video.save()
        
        return True
    except Video.DoesNotExist:
        print(f"Video with id {video_id} does not exist")
        return False
    except KeyError as e:
        print(f"Key error processing emotions: {str(e)}")
        try:
            video = Video.objects.get(id=video_id)
            video.status = 'failed'
            video.save()
        except:
            print(f"Could not update video status after KeyError")
        return False
    except Exception as e:
        print(f"Error analyzing video: {str(e)}")
        try:
            video = Video.objects.get(id=video_id)
            video.status = 'failed'
            video.save()
        except:
            print(f"Could not update video status after error")
        return False