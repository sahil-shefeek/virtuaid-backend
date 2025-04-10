import os
import numpy as np
from django.conf import settings
from celery import shared_task
from .models import Video, EmotionAnalysis, EmotionAnalysisSummary, EmotionTimeline
from .utils.emotion_detector import EmotionDetector
import logging

# Configure logger
logger = logging.getLogger(__name__)

@shared_task
def analyze_video_emotions(video_id, frame_rate=1.0):
    """
    Process video and detect emotions in each frame, then build emotion timeline
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
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found at path: {video_path}")
            video.status = 'failed'
            video.save()
            return False
        
        # Analyze video
        logger.info(f"Starting emotion analysis for video {video_id}")
        results = detector.analyze_video(video_path, frame_rate)
        
        if not results:
            logger.error(f"No analysis results returned for video {video_id}")
            video.status = 'failed'
            video.save()
            return False
            
        # Store individual frame results
        emotion_analyses = []
        
        # Define supported emotions for the new model
        supported_emotions = ['angry', 'sad', 'happy']
        
        # Initialize emotion sums and counts dictionaries with only supported emotions
        emotion_sums = {emotion: 0.0 for emotion in supported_emotions}
        emotion_counts = {emotion: 0 for emotion in supported_emotions}
        
        # Process each frame result
        for result in results:
            timestamp = result['timestamp']
            
            # Verify all required emotions are present in the result
            for emotion in supported_emotions:
                if emotion not in result:
                    logger.error(f"Missing emotion '{emotion}' in frame results. Got: {list(result.keys())}")
                    video.status = 'failed'
                    video.save()
                    return False
            
            # Create analysis object with only the emotions our model supports
            analysis_data = {
                'video': video,
                'timestamp': timestamp
            }
            
            # Find dominant emotion for this frame
            max_emotion = None
            max_value = -1
            
            # Add only the emotions from our new model
            for emotion in supported_emotions:
                analysis_data[emotion] = result[emotion]
                emotion_sums[emotion] += result[emotion]
                
                # Track the dominant emotion for this frame
                if result[emotion] > max_value:
                    max_value = result[emotion]
                    max_emotion = emotion
            
            if max_emotion:
                emotion_counts[max_emotion] += 1
            
            # Create EmotionAnalysis instance
            analysis = EmotionAnalysis(**analysis_data)
            emotion_analyses.append(analysis)
        
        # Bulk create all emotion analyses
        EmotionAnalysis.objects.bulk_create(emotion_analyses)
        
        # Calculate averages and create summary
        num_frames = len(results)
        if num_frames > 0:
            # Create emotion timeline segments
            create_emotion_timeline(video, emotion_analyses)
            
            # Calculate averages for summary
            emotion_avgs = {emotion: (emotion_sums[emotion] / num_frames) for emotion in supported_emotions}
            
            # Create summary object with only supported emotions
            summary_data = {
                'video': video,
                'emotion_counts': emotion_counts
            }
            
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
            
            logger.info(f"Completed emotion analysis for video {video_id}")
            return True
        else:
            logger.error(f"No frames processed for video {video_id}")
            video.status = 'failed'
            video.save()
            return False
            
    except Video.DoesNotExist:
        logger.error(f"Video with id {video_id} does not exist")
        return False
    except KeyError as e:
        logger.error(f"Key error processing emotions: {str(e)}")
        try:
            video = Video.objects.get(id=video_id)
            video.status = 'failed'
            video.save()
        except Exception as inner_e:
            logger.error(f"Could not update video status after KeyError: {str(inner_e)}")
        return False
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}", exc_info=True)
        try:
            video = Video.objects.get(id=video_id)
            video.status = 'failed'
            video.save()
        except Exception as inner_e:
            logger.error(f"Could not update video status after error: {str(inner_e)}")
        return False


def create_emotion_timeline(video, analyses):
    """
    Create emotion timeline segments from individual frame analyses
    Args:
        video: Video object
        analyses: List of EmotionAnalysis objects
    """
    if not analyses:
        return
    
    # Sort analyses by timestamp
    sorted_analyses = sorted(analyses, key=lambda x: x.timestamp)
    
    current_emotion = None
    segment_start = 0
    segment_frames = []
    emotion_segments = []
    
    # Process each analysis to find continuous emotion segments
    for i, analysis in enumerate(sorted_analyses):
        # Calculate dominant emotion for this frame
        emotions = {
            'angry': analysis.angry,
            'sad': analysis.sad,
            'happy': analysis.happy
        }
        dominant_emotion = max(emotions, key=emotions.get)
        confidence = emotions[dominant_emotion]
        
        # If this is the first frame or emotion changed
        if current_emotion is None or current_emotion != dominant_emotion:
            # If not the first frame, create a segment for the previous emotion
            if current_emotion is not None:
                end_time = analysis.timestamp
                
                # Create the emotion segment
                segment = EmotionTimeline(
                    video=video,
                    start_time=segment_start,
                    end_time=end_time,
                    duration=end_time - segment_start,
                    dominant_emotion=current_emotion,
                    confidence=sum(score for _, score in segment_frames) / len(segment_frames) if segment_frames else 0.0
                )
                emotion_segments.append(segment)
            
            # Start new segment
            current_emotion = dominant_emotion
            segment_start = analysis.timestamp
            segment_frames = [(dominant_emotion, confidence)]
        else:
            # Continue current segment
            segment_frames.append((dominant_emotion, confidence))
    
    # Add the last segment
    if current_emotion is not None and sorted_analyses:
        last_analysis = sorted_analyses[-1]
        
        segment = EmotionTimeline(
            video=video,
            start_time=segment_start,
            end_time=last_analysis.timestamp,
            duration=last_analysis.timestamp - segment_start,
            dominant_emotion=current_emotion,
            confidence=sum(score for _, score in segment_frames) / len(segment_frames) if segment_frames else 0.0
        )
        emotion_segments.append(segment)
    
    # Bulk create all emotion timeline segments
    if emotion_segments:
        EmotionTimeline.objects.bulk_create(emotion_segments)