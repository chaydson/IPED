﻿'''
# Python face recognition feature based on Face Recognition Project (https://pypi.org/project/face-recognition/)
# FaceRecognitionTask.py - By Rui Sant'Ana Junior and Luis Nassif
# Requirements: See https://github.com/sepinf-inc/IPED/wiki/User-Manual#facerecognition
# If enabled, you can search for faces from the analysis interface, check the options menu.
'''

#import face_recognition as fr
import os
import time
import subprocess
import threading, queue
import traceback
import platform

# configuration properties
enableProp = 'enableFaceRecognition'
configFile = 'FaceRecognitionConfig.txt'
numFaceRecognitionProcessesProp = 'numFaceRecognitionProcesses'
maxResolutionProp = 'maxResolution'
faceDetectionModelProp = 'faceDetectionModel'
upSamplingProp = 'upSampling'

# External process script
processScript = 'FaceRecognitionProcess.py'

# Maximum number of face recognition processes to run simultaneously
maxProcesses = None
numCreatedProcs = 0
numCreatedProcsLock = threading.Lock()

from java.lang import System
ipedRoot = System.getProperty('iped.root')

bin = 'python' if platform.system().lower() == 'windows' else 'python3'

detection_model = 'hog'
max_size = 1024
up_sampling = 1

firstInstance = True
processQueue = None
cache = {}

timeLock = threading.Lock()
detectTime = 0
featureTime = 0

def createProcessQueue():
    global processQueue, maxProcesses
    if processQueue is None:
        if maxProcesses is None:
            maxProcesses = int(max(1, numThreads / 2))
        processQueue = queue.Queue(maxProcesses)

def log_stderr(proc):
    for line in iter(proc.stderr.readline, b''):
        if proc.poll() is not None:
            break
        line = line.strip()
        if line:
            logger.info("[FaceRecognitionTask] Process-" + str(proc.pid) + " stderr: " + line)
    proc.stderr.close()

# Start external process, check if it is alive and ping to test communication
def createExternalProcess():
    proc = None
    for i in range(3):
        if proc is None or proc.poll() is not None:
            proc = subprocess.Popen([bin, os.path.join(ipedRoot, 'scripts', 'tasks', processScript), str(max_size), detection_model, str(up_sampling)], 
                                    stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if pingExternalProcess(proc):
            from threading import Thread
            t = Thread(target=log_stderr, args=(proc,))
            t.daemon = True
            t.start()
            return proc
        else:
            proc.kill()
            proc = None
            
    raise Exception("Error creating external face recognition process!")

def pingExternalProcess(proc):
    try:
        print(ping, file=proc.stdin, flush=True)
        line = proc.stdout.readline().strip()
        if line == ping:
            return True
    except:
        traceback.print_exc()
    return False

class FaceRecognitionTask:

    enabled = False
    videoSubitems = False
    
    def isEnabled(self):
        return FaceRecognitionTask.enabled
    
    def getConfigurables(self):
        from iped.engine.config import DefaultTaskPropertiesConfig
        return [DefaultTaskPropertiesConfig(enableProp, configFile)]
    
    # This method is executed before starting the processing of items.
    def init(self, configuration):
        taskConfig = configuration.getTaskConfigurable(configFile)
        FaceRecognitionTask.enabled = taskConfig.isEnabled()
        if not FaceRecognitionTask.enabled:
            return
        
        from iped.engine.config import VideoThumbsConfig
        videoConfig = configuration.findObject(VideoThumbsConfig);
        FaceRecognitionTask.videoSubitems = videoConfig.getVideoThumbsSubitems();
        
        global fp, terminate, imgError, ping
        import FaceRecognitionProcess as fp
        terminate = fp.terminate
        imgError = fp.imgError
        ping = fp.ping
        
        global np
        import numpy as np
        
        # check if was called from gui the first time
        global maxProcesses, firstInstance
        # load configuration properties
        extraProps = taskConfig.getConfiguration()
        numProcs = extraProps.getProperty(numFaceRecognitionProcessesProp)
        if firstInstance and numProcs is not None:
            maxProcesses = int(numProcs)
        firstInstance = False
        
        # configure embedded python path on windows
        if platform.system().lower() == 'windows':
            global bin
            bin = os.path.join(ipedRoot, 'python', 'pythonw')
        
        numProcs = extraProps.getProperty(numFaceRecognitionProcessesProp)
        if maxProcesses is None and numProcs is not None:
            maxProcesses = int(numProcs)
        maxResolution = extraProps.getProperty(maxResolutionProp)
        global max_size, detection_model, up_sampling
        if maxResolution is not None:
            max_size = int(maxResolution)
        faceDetectionModel = extraProps.getProperty(faceDetectionModelProp)
        if faceDetectionModel is not None:
            detection_model = faceDetectionModel
        upSampling = extraProps.getProperty(upSamplingProp)
        if upSampling is not None:
            up_sampling = int(upSampling)
        
        createProcessQueue()
        return
            
    # It is executed after processing all items in case.
    def finish(self):
        #terminate subprocess
        if not processQueue.empty():
            proc = processQueue.get(block=True)
            if proc.poll() is None:
                try:
                    print(terminate, file=proc.stdin, flush=True)
                    proc.wait(2)
                except:
                    proc.kill()
                with numCreatedProcsLock:
                    global numCreatedProcs
                    numCreatedProcs -= 1
        
        with timeLock:
            global detectTime, featureTime
            if detectTime + featureTime >= 0:
                logger.info('[FaceRecognitionTask] Time(s) to detect faces: ' + str(detectTime / maxProcesses))
                logger.info('[FaceRecognitionTask] Time(s) to get face features: ' + str(featureTime / maxProcesses))
                detectTime = -1
                featureTime = -1
    
    # Needed because tuples cause ClassNotFoundException on java side later
    def convertTuplesToList(self, tuples):
        result = []
        for i in tuples:
            result.append(list(i))
        return result
    
    def cacheResults(self, hash, locations, encodings, count):
        cache[hash + '_locations'] = locations
        cache[hash + '_encodings'] = encodings
        cache[hash + '_count'] = count
    
    # This function is executed on all case items
    def process(self, item):
    
        hash = item.getHash()
        # Only image type items are processed
        if hash is None or not item.getExtraAttribute('hasThumb'):
            return
        
        from iped.properties import ExtraProperties

        # don't process it again (in the report generation for example)
        face_count = item.getExtraAttribute(ExtraProperties.FACE_COUNT)
        if face_count is not None:
            return

        # reuse cached results
        face_locations = cache.get(hash + '_locations')
        face_encodings = cache.get(hash + '_encodings')
        face_count = cache.get(hash + '_count')
        if face_count is not None:
            if face_count >= 0:
                item.setExtraAttribute(ExtraProperties.FACE_COUNT, face_count)
                if face_locations is not None and face_encodings is not None:
                    if len(face_locations) > 0 and len(face_encodings) > 0:
                        item.setExtraAttribute(ExtraProperties.FACE_LOCATIONS, face_locations)
                        item.setExtraAttribute(ExtraProperties.FACE_ENCODINGS, face_encodings)
            return

        # Load absolute path
        isVideo = False
        mediaType = item.getMediaType().toString()
        if mediaType.startswith('image'):
            if item.getViewFile() is not None and os.path.exists(item.getViewFile().getAbsolutePath()):
                img_path = item.getViewFile().getAbsolutePath()
            else:
                img_path = item.getTempFile().getAbsolutePath()
        elif mediaType.startswith('video') and not FaceRecognitionTask.videoSubitems:
            img_path = item.getViewFile().getAbsolutePath()
            isVideo = True
        else:
            return
    
        try:
            # Get tiff:Orientation attribute
            tiff_orient = int(item.getMetadata().get("image:tiff:Orientation"))
        except:
            # If item has no tiff:Orientation attribute
            tiff_orient = 1

        
        # creates process in parallel
        numCreatedProcsLock.acquire()
        global numCreatedProcs
        if numCreatedProcs < maxProcesses:
            numCreatedProcs += 1
            numCreatedProcsLock.release()
            proc = createExternalProcess()
            processQueue.put(proc, block=True)
        else:
            numCreatedProcsLock.release()
        
        
        try:
            proc = processQueue.get(block=True)
            if not pingExternalProcess(proc):
                proc.kill()
                proc = createExternalProcess()
            
            print(img_path, file=proc.stdin, flush=True)
            if not isVideo:
                print(str(tiff_orient), file=proc.stdin, flush=True)
            else:
                print(fp.video, file=proc.stdin, flush=True)
                    
            t1 = time.time()
            #face_locations = fr.face_locations(img)
            
            line = proc.stdout.readline().strip()

            if not line:
                time.sleep(3)
                status = str(proc.poll())
                logger.warn("[FaceRecognitionTask] Unexpected error from external process while processing {} ({} bytes) exit status=" + status, item.getPath(), item.getLength())
                proc.kill()
                proc = createExternalProcess()
                return

            if line == imgError:
                logger.info("[FaceRecognitionTask] Error loading image {} ({} bytes)", item.getPath(), item.getLength())
                self.cacheResults(hash, [], [], -1)
                return
                
            num_faces = int(line)
            
            t2 = time.time()
            with timeLock:
                global detectTime
                detectTime += t2 - t1
            
            if num_faces == 0:
                item.setExtraAttribute(ExtraProperties.FACE_COUNT, 0)
                self.cacheResults(hash, [], [], 0)
                return
            
            face_locations = []
            for i in range(num_faces):
                line = proc.stdout.readline()
                face_locations.append(eval(line))
            #print('locations ' + str(face_locations))
            
            #face_encodings = fr.face_encodings(img, face_locations)
            
            face_encodings = []
            for i in range(num_faces):
                list = []
                for j in range(128):
                    line = proc.stdout.readline()
                    list.append(float(line))
                np_array = np.array(list)
                face_encodings.append(np_array)
            
            #print('encodings ' + str(face_encodings))
            
            t3 = time.time()
            with timeLock:
                global featureTime
                featureTime += t3 - t2
        
        finally:
            processQueue.put(proc, block=True)
        
        face_locations = self.convertTuplesToList(face_locations)
        face_count = len(face_locations)

        item.setExtraAttribute(ExtraProperties.FACE_LOCATIONS, face_locations)
        item.setExtraAttribute(ExtraProperties.FACE_ENCODINGS, face_encodings)
        item.setExtraAttribute(ExtraProperties.FACE_COUNT, face_count)
        
        self.cacheResults(hash, face_locations, face_encodings, face_count)
