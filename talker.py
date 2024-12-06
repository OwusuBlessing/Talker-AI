import os
import asyncio
import shutil
from typing import Tuple, Optional
from dataclasses import dataclass
import random
import nest_asyncio
from LLM import LLM
from ASR import WhisperASR
from TFG import SadTalker
from TTS import EdgeTTS
# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


import os
import asyncio
import shutil
from typing import Tuple, Optional
from dataclasses import dataclass
import random
import nest_asyncio
from LLM import LLM
import nest_asyncio
from ASR import WhisperASR
from TFG import SadTalker
from TTS import EdgeTTS
# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

@dataclass
class TalkerConfig:
    source_image: str = 'example.png'
    blink_every: bool = True
    size_of_image: int = 256
    preprocess_type: str = 'crop'
    facerender: str = 'facevid2vid'
    enhancer: bool = False
    is_still_mode: bool = False
    pic_path: str = "./inputs/girl.png"
    crop_pic_path: str = "./inputs/first_frame_dir_girl/girl.png"
    first_coeff_path: str = "./inputs/first_frame_dir_girl/girl.mat"
    crop_info: tuple = ((403, 403), (19, 30, 502, 513), 
                       [40.05956541381802, 40.17324339233366, 
                        443.7892505041507, 443.9029284826663])
    exp_weight: float = 1.0
    use_ref_video: bool = False
    ref_video: Optional[str] = None
    ref_info: str = 'pose'
    use_idle_mode: bool = False
    length_of_audio: int = 5
    batch_size: int = 2
    fps: int = 20
    voice_id:str=None
    audio_path:str= None


class LinlyTalker:
    def __init__(self, config):
        self.config = config
        
        # Initialize core components
        self.llm = LLM(mode='offline').init_model('Qwen', 'Qwen/Qwen-1_8B-Chat')
        self.talker = SadTalker(lazy_load=True)
        self.asr = WhisperASR('base')
        self.tts = EdgeTTS()
        
        # Initialize event loop
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file to text using WhisperASR
        """
        try:
            return self.asr.transcribe(audio_path)
        except Exception as e:
            print(f"ASR Error: {e}")
            return None

    async def _generate_speech_async(self, 
                                   text: str, 
                                   voice: str = 'en-US-JennyNeural',
                                   rate: int = 0,
                                   volume: int = 100,
                                   pitch: int = 0,
                                   output_path: str = 'output.wav') -> Tuple[str, str]:
        """
        Async function to generate speech
        """
        try:
            communicate = await asyncio.create_subprocess_exec(
                'edge-tts',
                '--text', text,
                '--voice', voice,
                '--write-media', output_path,
                '--write-subtitles', output_path.replace('.wav', '.vtt'),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await communicate.communicate()
            
            return output_path, output_path.replace('.wav', '.vtt')
        except Exception as e:
            print(f"TTS Error: {e}")
            return None, None

    def generate_speech(self, 
                       text: str, 
                       voice: str = 'en-US-JennyNeural',
                       rate: int = 0,
                       volume: int = 100,
                       pitch: int = 0,
                       output_path: str = 'output.wav') -> Tuple[str, str]:
        """
        Generate speech from text using EdgeTTS
        Returns tuple of (audio_path, subtitle_path)
        """
        try:
            return self.loop.run_until_complete(
                self._generate_speech_async(text, voice, rate, volume, pitch, output_path)
            )
        except Exception as e:
            print(f"Speech generation error: {e}")
            return None, None

    def generate_response(self, question: str) -> str:
        """
        Generate text response using LLM
        """
        try:
            return self.llm.generate(question)
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

    def generate_talking_video(self, 
                               text=None,
                             output_path: str = 'output_video.mp4',
                             voice: str = 'en-US-JennyNeural',
                             rate: int = 0,
                             volume: int = 100,
                             pitch: int = 0) -> Tuple[str, str]:
        """
        Generate a talking head video from text input
        Returns tuple of (video_path, subtitle_path)
        """
        try:
            # Generate response and audio
            #response = self.generate_response(text)
            #if not response:
                #return None, None
                
            #audio_path, subtitle_path = self.generate_speech(
            #    response, voice, rate, volume, pitch
           # )
           

            # Random pose style for variety
            pose_style = random.randint(0, 45)
            
            # Generate video using SadTalker
            video_path = self.talker.test(
                self.config.pic_path,
                self.config.crop_pic_path,
                self.config.first_coeff_path,
                self.config.crop_info,
                self.config.source_image,
                self.config.audio_path,
                self.config.preprocess_type,
                self.config.is_still_mode,
                self.config.enhancer,
                self.config.batch_size,
                self.config.size_of_image,
                pose_style,
                self.config.facerender,
                self.config.exp_weight,
                self.config.use_ref_video,
                self.config.ref_video,
                self.config.ref_info,
                self.config.use_idle_mode,
                self.config.length_of_audio,
                self.config.blink_every,
                fps=self.config.fps
            )
            
            # Copy the generated video to the desired output path
            if video_path and os.path.exists(video_path):
                shutil.move(video_path, output_path)
                return output_path
            return None, None
            
        except Exception as e:
            print(f"Video generation error: {e}")
            return None, None
