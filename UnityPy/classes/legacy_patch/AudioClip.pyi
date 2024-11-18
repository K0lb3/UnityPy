from typing import Dict, List, Optional

from UnityPy.classes.generated import SampleClip, StreamedResource

class AudioClip(SampleClip):
  m_Name: str
  m_3D: Optional[bool] = None
  m_Ambisonic: Optional[bool] = None
  m_AudioData: Optional[List[int]] = None
  m_BitsPerSample: Optional[int] = None
  m_Channels: Optional[int] = None
  m_CompressionFormat: Optional[int] = None
  m_Format: Optional[int] = None
  m_Frequency: Optional[int] = None
  m_IsTrackerFormat: Optional[bool] = None
  m_Legacy3D: Optional[bool] = None
  m_Length: Optional[float] = None
  m_LoadInBackground: Optional[bool] = None
  m_LoadType: Optional[int] = None
  m_PreloadAudioData: Optional[bool] = None
  m_Resource: Optional[StreamedResource] = None
  m_Stream: Optional[int] = None
  m_SubsoundIndex: Optional[int] = None
  m_Type: Optional[int] = None
  m_UseHardware: Optional[bool] = None

  @property
  def extension(self) -> str: ...

  @property
  def samples(self) -> Dict[str, bytes]: ...
