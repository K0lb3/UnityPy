import os
from helpers import ImportHelper
from EndianBinaryReader import EndianBinaryReader
from Progress import Progress
from Logger import Logger
from files import BundleFile, SerializedFile, WebFile
from ObjectReader import ObjectReader
from Object import Object
import classes

FileType = ImportHelper.FileType


class AssetsManager():
	assetsFileList = []
	assetsFileIndexCache = {}
	resourceFileReaders = {}
	
	importFiles = []
	importFilesHash = []
	assetsFileListHash = []
	Progress = Progress()
	Logger = Logger()
	
	def LoadFiles(self, files):
		path = os.path.dirname(files[0])
		ImportHelper.MergeSplitAssets(path)
		toReadFile = ImportHelper.ProcessingSplitFiles(files)
		self.Load(toReadFile)
	
	def LoadFolder(self, path):
		ImportHelper.MergeSplitAssets(path, True)
		files = ImportHelper.ListAllFiles(path)
		toReadFile = ImportHelper.ProcessingSplitFiles(files)
		self.Load(toReadFile)
	
	def Load(self, files):
		for f in files:
			self.importFiles.append(f)
			self.importFilesHash.append(os.path.basename(f).upper())
		
		self.Progress.Reset()
		# use a for loop because list size can change
		for i, f in enumerate(self.importFiles):
			self.LoadFile(f)
			self.Progress.Report(i + 1, len(self.importFiles))
		
		self.importFiles = []
		self.importFilesHash = []
		self.assetsFileListHash = []
		
		self.ReadAssets()
	
	# self.ProcessGameObject()
	
	def LoadFile(self, fullName):
		typ, reader = ImportHelper.CheckFileType(fullName)
		if typ == FileType.AssetsFile:
			self.LoadAssetsFile(fullName, reader)
		elif typ == FileType.BundleFile:
			self.LoadBundleFile(fullName, reader)
		elif FileType.WebFile:
			self.LoadWebFile(fullName, reader)
	
	def LoadAssetsFile(self, fullName, reader):
		fileName = os.path.basename(fullName)
		if fileName.upper() not in self.assetsFileListHash:
			self.Logger.Info(f"Loading {fullName}")
			try:
				assetsFile = SerializedFile(self, fullName, reader)
				self.assetsFileList.append(assetsFile)
				self.assetsFileListHash.append(assetsFile.upperFileName)
				
				for sharedFile in assetsFile.m_Externals:
					sharedFilePath = os.path.join(os.path.dirname(fullName), sharedFile.fileName)
					sharedFileName = sharedFile.fileName
					
					if sharedFileName.upper() not in self.importFilesHash:
						if not os.path.exists(sharedFilePath):
							findFiles = [f for f in ImportHelper.ListAllFiles(os.path.dirname(fullName)) if sharedFileName in f]
							if findFiles:
								sharedFilePath = findFiles[0]
						
						if os.path.exists(sharedFilePath):
							self.importFiles.append(sharedFilePath)
							self.importFilesHash.append(sharedFileName.upper())
			
			except:
				reader.Dispose()
				self.Logger.Error(f"Unable to load assets file {fileName}")
		else:
			reader.Dispose()
		return assetsFile
	
	def LoadAssetsFromMemory(self, fullName, reader, originalPath, unityVersion = None):
		upperFileName = os.path.basename(fullName).upper()
		if upperFileName not in self.assetsFileListHash:
			try:
				assetsFile = SerializedFile(self, fullName, reader)
				assetsFile.originalPath = originalPath
				if assetsFile.header.m_Version < 7:
					assetsFile.SetVersion(unityVersion)
				self.assetsFileList.append(assetsFile)
				self.assetsFileListHash.append(upperFileName)
			except:
				if '.RESS' != upperFileName[-5:]:
					self.Logger.Error(f"Unable to load assets file {upperFileName} from {originalPath}")
			finally:
				self.resourceFileReaders[upperFileName] = reader
	
	def LoadBundleFile(self, fullName, reader, parentPath = None):
		fileName = os.path.basename(fullName)
		self.Logger.Info(f"Loading {fullName}")
		try:
			bundleFile = BundleFile(reader, fullName)
			for f in bundleFile.fileList:
				dummyPath = os.path.join(os.path.dirname(fullName), f.fileName)
				self.LoadAssetsFromMemory(dummyPath, EndianBinaryReader(f.stream), fullName if parentPath else bundleFile.versionEngine)
		except:
			string = f"Unable to load bundle file {fileName}"
			if parentPath:
				string += f" from {os.path.basename(parentPath)}"
			self.Logger.Error(string)
		finally:
			reader.Dispose()
		return bundleFile
	
	def LoadWebFile(self, fullName, reader):
		fileName = os.path.basename(fullName)
		self.Logger.Info(f"Loading {fullName}")
		try:
			webFile = WebFile(reader)
			for f in webFile.fileList:
				dummyPath = os.path.join(os.path.dirname(fullName), f.fileName)
				typ, reader = ImportHelper.CheckFileType(f.stream)
				if typ == FileType.AssetsFile:
					self.LoadAssetsFromMemory(dummyPath, reader, fullName)
				elif typ == FileType.BundleFile:
					self.LoadBundleFile(dummyPath, reader, fullName)
				elif typ == FileType.WebFile:
					self.LoadWebFile(dummyPath, reader)
		
		except:
			self.Logger.Error(f"Unable to load web file {fileName}")
		finally:
			reader.Dispose()
		return webFile
	
	def Clear(self):
		for assetsFile in self.assetsFileList:
			assetsFile.Objects = []
			assetsFile.reader.Close()
		self.assetsFileList = []
		
		for resourceFileReader in self.resourceFileReaders:
			resourceFileReader.Value.Close()
		
		self.resourceFileReaders = {}
		self.assetsFileIndexCache = []
	
	def ReadAssets(self):
		self.Logger.Info("Read assets...")
		progressCount = sum([len(af.m_Objects) for af in self.assetsFileList])
		i = 0
		self.Progress.Reset()
		for assetsFile in self.assetsFileList:
			assetsFile.Objects = {}
			for objectInfo in assetsFile.m_Objects:
				objectReader = ObjectReader(assetsFile.reader, assetsFile, objectInfo)
				if objectReader.type != classes.Object:
					print(objectReader.type)
					print()
				assetsFile.Objects[objectInfo.m_PathID] = objectReader.Read()
				self.Progress.Report(i, progressCount)


'''
	private void ReadAssets()
	{
		Logger.Info("Read assets...");

		var progressCount = assetsFileList.Sum(x => x.m_Objects.Count);
		int i = 0;
		Progress.Reset();
		foreach (var assetsFile in assetsFileList)
		{
			assetsFile.Objects = new Dictionary<long, Object>(assetsFile.m_Objects.Count);
			foreach (var objectInfo in assetsFile.m_Objects)
			{
				var objectReader = new ObjectReader(assetsFile.reader, assetsFile, objectInfo);
				switch (objectReader.type)
				{
					case ClassIDType.Animation:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Animation(objectReader));
						break;
					case ClassIDType.AnimationClip:
						assetsFile.Objects.Add(objectInfo.m_PathID, new AnimationClip(objectReader));
						break;
					case ClassIDType.Animator:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Animator(objectReader));
						break;
					case ClassIDType.AnimatorController:
						assetsFile.Objects.Add(objectInfo.m_PathID, new AnimatorController(objectReader));
						break;
					case ClassIDType.AnimatorOverrideController:
						assetsFile.Objects.Add(objectInfo.m_PathID, new AnimatorOverrideController(objectReader));
						break;
					case ClassIDType.AssetBundle:
						assetsFile.Objects.Add(objectInfo.m_PathID, new AssetBundle(objectReader));
						break;
					case ClassIDType.AudioClip:
						assetsFile.Objects.Add(objectInfo.m_PathID, new AudioClip(objectReader));
						break;
					case ClassIDType.Avatar:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Avatar(objectReader));
						break;
					case ClassIDType.Font:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Font(objectReader));
						break;
					case ClassIDType.GameObject:
						assetsFile.Objects.Add(objectInfo.m_PathID, new GameObject(objectReader));
						break;
					case ClassIDType.Material:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Material(objectReader));
						break;
					case ClassIDType.Mesh:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Mesh(objectReader));
						break;
					case ClassIDType.MeshFilter:
						assetsFile.Objects.Add(objectInfo.m_PathID, new MeshFilter(objectReader));
						break;
					case ClassIDType.MeshRenderer:
						assetsFile.Objects.Add(objectInfo.m_PathID, new MeshRenderer(objectReader));
						break;
					case ClassIDType.MonoBehaviour:
						assetsFile.Objects.Add(objectInfo.m_PathID, new MonoBehaviour(objectReader));
						break;
					case ClassIDType.MonoScript:
						assetsFile.Objects.Add(objectInfo.m_PathID, new MonoScript(objectReader));
						break;
					case ClassIDType.MovieTexture:
						assetsFile.Objects.Add(objectInfo.m_PathID, new MovieTexture(objectReader));
						break;
					case ClassIDType.PlayerSettings:
						assetsFile.Objects.Add(objectInfo.m_PathID, new PlayerSettings(objectReader));
						break;
					case ClassIDType.RectTransform:
						assetsFile.Objects.Add(objectInfo.m_PathID, new RectTransform(objectReader));
						break;
					case ClassIDType.Shader:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Shader(objectReader));
						break;
					case ClassIDType.SkinnedMeshRenderer:
						assetsFile.Objects.Add(objectInfo.m_PathID, new SkinnedMeshRenderer(objectReader));
						break;
					case ClassIDType.Sprite:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Sprite(objectReader));
						break;
					case ClassIDType.SpriteAtlas:
						assetsFile.Objects.Add(objectInfo.m_PathID, new SpriteAtlas(objectReader));
						break;
					case ClassIDType.TextAsset:
						assetsFile.Objects.Add(objectInfo.m_PathID, new TextAsset(objectReader));
						break;
					case ClassIDType.Texture2D:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Texture2D(objectReader));
						break;
					case ClassIDType.Transform:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Transform(objectReader));
						break;
					case ClassIDType.VideoClip:
						assetsFile.Objects.Add(objectInfo.m_PathID, new VideoClip(objectReader));
						break;
					default:
						assetsFile.Objects.Add(objectInfo.m_PathID, new Object(objectReader));
						break;
				}

				Progress.Report(++i, progressCount);
			}
		}
	}

	private void ProcessGameObject()
	{
		Logger.Info("Process GameObject...");

		foreach (var assetsFile in assetsFileList)
		{
			foreach (var obj in assetsFile.Objects.Values)
			{
				if (obj is GameObject m_GameObject)
				{
					foreach (var pptr in m_GameObject.m_Components)
					{
						if (pptr.TryGet(out var m_Component))
						{
							switch (m_Component)
							{
								case Transform m_Transform:
									m_GameObject.m_Transform = m_Transform;
									break;
								case MeshRenderer m_MeshRenderer:
									m_GameObject.m_MeshRenderer = m_MeshRenderer;
									break;
								case MeshFilter m_MeshFilter:
									m_GameObject.m_MeshFilter = m_MeshFilter;
									break;
								case SkinnedMeshRenderer m_SkinnedMeshRenderer:
									m_GameObject.m_SkinnedMeshRenderer = m_SkinnedMeshRenderer;
									break;
								case Animator m_Animator:
									m_GameObject.m_Animator = m_Animator;
									break;
								case Animation m_Animation:
									m_GameObject.m_Animation = m_Animation;
									break;
							}
						}
					}
				}
			}
		}
	}
}
}
'''
