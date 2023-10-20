import FWCore.ParameterSet.Config as cms
import os, sys, imp, re
import FWCore.ParameterSet.VarParsing as VarParsing

#sys.path(".")

#new options to make everything easier for batch

############################################################
### SETUP OPTIONS

options = VarParsing.VarParsing('standard')
options.register('debug',
                 False,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.bool,
                 "DEBUG flag")
options.register('jsonFile',
                 "",
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "path and name of the json file")
options.register('step',
                 "RECOTIMEANALYSIS",
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "Do reco, time analysis or both, RECO|TIMEANALYSIS|RECOTIMEANALYSIS")
options.register('timealgo',
                 'RatioMethod',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "Timing algo used in multifit producer")
options.register('skipEvents',
                 0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.int,
                 "Skip this many events")
options.register('offset',
                 0.0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.float,
                 "add this to each crystal time")
options.register('minEnergyEB',
                 0.0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.float,
                 "add this to minimum energy threshold")
options.register('minEnergyEE',
                 0.0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.float,
                 "add this to minimum energy threshold")
options.register('minChi2EB',
                 50.0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.float,
                 "add this to minimum chi2 threshold")
options.register('minChi2EE',
                 50.0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.float,
                 "add this to minimum chi2 threshold")
options.register('isSplash',
                 0,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.int,
                 "0=false, 1=true"
                 )
options.register('streamName',
                 'AlCaPhiSym',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "type of stream: AlCaPhiSym or AlCaP0")
options.register('globaltag',
                 '130X_dataRun3_Prompt_v2',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "Global tag to use, no default")
options.register('useCustomTimeCalib',
                 False,
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.bool,
                 "Use custom time calibration record. By default, it uses CondDB entry.")
options.register('sqliteRecord',
                 'file:../test/template/tmp.sqlite',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "Path to the sqlite file contianing time calib record.")
options.register('loneBunch',
                   0,
                   VarParsing.VarParsing.multiplicity.singleton,
                   VarParsing.VarParsing.varType.int,
                   "0=No, 1=Yes"
                 )
options.register('outputFile',
                 'output/ecalTiming.root',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                "outputFile")
options.register('dbtag',
                 'EcalTimeCalibConstants_v01_prompt',
                 VarParsing.VarParsing.multiplicity.singleton,
                 VarParsing.VarParsing.varType.string,
                 "DB tag (EcalTimeCalibConstants_v01_prompt/EcalTimeCalibConstants_v3_hlt)")
                 
### setup any defaults you want
#options.output=options.outputFile
options.secondaryOutput="ntuple.root"

if(options.streamName=="AlCaP0"):
    print("stream ",options.streamName) #options.files = "/store/data/Commissioning2015/AlCaP0/RAW/v1/000/246/342/00000/048ECF48-F906-E511-95AC-02163E011909.root"
elif(options.streamName=="AlCaPhiSym"):
    print("stream ",options.streamName) #options.files = "/store/data/Commissioning2015/AlCaPhiSym/RAW/v1/000/244/768/00000/A8219906-44FD-E411-8DA9-02163E0121C5.root"
else: 
    print("stream ",options.streamName," not foreseen")
    exit

### get and parse the command line arguments
options.parseArguments()
print(options)

processname = options.step

doReco = True
doAnalysis = True
if "RECO" not in processname:
    doReco = False
if "TIME" not in processname:
    doAnalysis = False

from Configuration.Eras.Era_Run3_cff import Run3
process = cms.Process(processname, Run3)

# if the one file is a folder, grab all the files in it that are RECO
if len(options.files) == 1 and options.files[0][-1] == '/' and not doReco:
    from EcalTiming.EcalTiming.storeTools_cff import fillFromStore
    files = fillFromStore(options.files[0])
    options.files.pop()
    options.files = [ f for f in files if "RECO" in f and "numEvent" not in f]


process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.MessageLogger.cerr.FwkReport.reportEvery = cms.untracked.int32(10000)

process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_38T_cff')

#import Electronics mapping
process.load("Geometry.EcalCommonData.EcalOnly_cfi")
process.load("Geometry.EcalMapping.EcalMapping_cfi")
process.load("Geometry.EcalMapping.EcalMappingRecord_cfi")

if(options.isSplash==1):
    ## Get Cosmic Reconstruction
    process.load('Configuration/StandardSequences/ReconstructionCosmics_cff')
    process.caloCosmics.remove(process.hbhereco)
    process.caloCosmics.remove(process.hcalLocalRecoSequence)
    process.caloCosmics.remove(process.hfreco)
    process.caloCosmics.remove(process.horeco)
    process.caloCosmics.remove(process.zdcreco)
    #process.caloCosmics.remove(process.ecalClusters)
    process.caloCosmicOrSplashRECOSequence = cms.Sequence(process.caloCosmics)#+ process.egammaCosmics)
else:
    process.load('Configuration/StandardSequences/Reconstruction_cff')
    process.recoSequence = cms.Sequence(process.calolocalreco)#+ process.egammaCosmics)

process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load('EcalTiming.EcalTiming.ecalLocalRecoSequenceAlCaStream_cff')
process.load('EcalTiming.EcalTiming.ecalLocalRecoSequenceAlCaP0Stream_cff')

if(options.streamName=="AlCaP0"):
    process.ecalMultiFitUncalibRecHit.cpu.EBdigiCollection = cms.InputTag("hltAlCaPi0EBRechitsToDigis","pi0EBDigis")
    process.ecalMultiFitUncalibRecHit.cpu.EEdigiCollection = cms.InputTag("hltAlCaPi0EERechitsToDigis","pi0EEDigis")
else:
    process.ecalMultiFitUncalibRecHit.cpu.EBdigiCollection = cms.InputTag("hltEcalPhiSymFilter","phiSymEcalDigisEB")
    process.ecalMultiFitUncalibRecHit.cpu.EEdigiCollection = cms.InputTag("hltEcalPhiSymFilter","phiSymEcalDigisEE")


## Raw to Digi
process.load('Configuration/StandardSequences/RawToDigi_Data_cff')

## HLT Filter Splash
import HLTrigger.HLTfilters.hltHighLevel_cfi
process.spashesHltFilter = HLTrigger.HLTfilters.hltHighLevel_cfi.hltHighLevel.clone(
    throw = cms.bool(False),
    #HLTPaths = ['HLT_EG20*', 'HLT_SplashEcalSumET', 'HLT_Calibration','HLT_EcalCalibration','HLT_HcalCalibration','HLT_Random','HLT_Physics','HLT_HcalNZS','HLT_SplashEcalSumET','HLTriggerFinalPath' ]
    HLTPaths = ['*']
)

# GLOBAL-TAG
from CondCore.CondDB.CondDB_cfi import *
CondDBSetup = CondDB.clone()
CondDBSetup.__delattr__('connect')


if (options.useCustomTimeCalib): 
    process.GlobalTag = cms.ESSource("PoolDBESSource",
                                 CondDBSetup,
                                 globaltag = cms.string(options.globaltag),
                                 connect = cms.string('frontier://FrontierProd/CMS_CONDITIONS'),
                                 toGet = cms.VPSet(
                                    cms.PSet(
                                        record = cms.string('EcalTimeCalibConstantsRcd'),
                                        tag = cms.string(options.dbtag),
                                        connect = cms.string(options.sqliteRecord),
                                        )
                                    )
                                 )
else:
    process.GlobalTag = cms.ESSource("PoolDBESSource",
                                     CondDBSetup,
                                     globaltag = cms.string(options.globaltag),
                                     connect = cms.string('frontier://FrontierProd/CMS_CONDITIONS'),
                                     toCopy = cms.VPSet(
                                     cms.PSet(
                                         record = cms.string('EcalTimeCalibConstantsRcd'),
                                         connect = cms.string('sqlite_file:tmp.db')
                                         )
                                      )
                                     )

    print(process.GlobalTag.__dict__)

# Adjustments depending on timing algorithm
if options.timealgo == "crossCorrelationMethod":
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.timealgo = cms.string(options.timealgo)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain12pEB = cms.double(2.5)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain12mEB = cms.double(2.5)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain61pEB = cms.double(2.5)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain61mEB = cms.double(2.5)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.crossCorrelationTimeShiftWrtRations = cms.double(0.0)
elif options.timealgo == "RatioMethod":
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.timealgo = cms.string(options.timealgo)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain12pEB = cms.double(5.)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain12mEB = cms.double(5.)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain61pEB = cms.double(5.)
    process.ecalMultiFitUncalibRecHit.cpu.algoPSet.outOfTimeThresholdGain61mEB = cms.double(5.)

## Process Digi To Raw Step
process.digiStep = cms.Sequence(process.ecalDigis  + process.ecalPreshowerDigis)

## Process Reco
# enable the TrigReport and TimeReport
process.options = cms.untracked.PSet(
    wantSummary = cms.untracked.bool(True),
    SkipEvent = cms.untracked.vstring('ProductNotFound')
)

SkipEvent = cms.untracked.vstring('ProductNotFound','EcalProblem')

# dbs search --query "find file where dataset=/ExpressPhysics/BeamCommissioning09-Express-v2/FEVT and run=124020" | grep store | awk '{printf "\"%s\",\n", $1}'
# Input source

#options.files = "file:/eos/cms//store/data/Run2023B/AlCaPhiSym/RAW/v1/000/366/873/00000/0a336950-1fbb-46be-bd5a-be8bc0f74c81.root"
print("source files:",options.files)
process.source = cms.Source("PoolSource",
    secondaryFileNames = cms.untracked.vstring(),
    fileNames = cms.untracked.vstring(options.files),
    skipEvents = cms.untracked.uint32(options.skipEvents)
)

if(len(options.jsonFile) > 0):
    import FWCore.PythonUtilities.LumiList as LumiList
    process.source.lumisToProcess = LumiList.LumiList(filename = options.jsonFile).getVLuminosityBlockRange()



recofile = str(options.output)
recofile = recofile[:recofile.find(".root")] + "_RECO.root"

# Output definition
process.RECOoutput = cms.OutputModule("PoolOutputModule",
                                      splitLevel = cms.untracked.int32(0),
                                      eventAutoFlushCompressedSize = cms.untracked.int32(5242880),
                                      outputCommands = cms.untracked.vstring('drop *',"keep *_EcalTimingEvents_*_*"),
                                      fileName = cms.untracked.string(recofile),
                                      dataset = cms.untracked.PSet(
                                          filterName = cms.untracked.string(''),
                                          dataTier = cms.untracked.string('RECO')
                                          )
                                       )


if doAnalysis:
    ## Histogram files
    process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string(options.outputFile),
                                   closeFileFast = cms.untracked.bool(True)
                                   )

### NumBer of events
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(options.maxEvents))

#DUMMY RECHIT
process.dummyHits = cms.EDProducer("DummyRechitDigis",
                                    doDigi = cms.untracked.bool(True),
                                    # rechits
                                    barrelHitProducer      = cms.InputTag('hltAlCaPi0EBUncalibrator','pi0EcalRecHitsEB' ,"HLT"),
                                    endcapHitProducer      = cms.InputTag('hltAlCaPi0EEUncalibrator','pi0EcalRecHitsEE' ,"HLT"),
                                    barrelRecHitCollection = cms.untracked.string("dummyBarrelRechitsPi0"),
                                    endcapRecHitCollection = cms.untracked.string("dummyEndcapRechitsPi0"),
                                    # digis
                                    barrelDigis            = cms.InputTag('hltAlCaPi0EBRechitsToDigis','pi0EBDigis',"HLT"),
                                    endcapDigis            = cms.InputTag('hltAlCaPi0EERechitsToDigisLowPU','pi0EEDigis',"HLT"), #changed hltAlCaPi0EERechitsToDigis in LowPU....changed in the file -.-
                                    barrelDigiCollection   = cms.untracked.string("dummyBarrelDigisPi0"),
                                    endcapDigiCollection   = cms.untracked.string("dummyEndcapDigisPi0"))

##ADDED
# TRIGGER RESULTS FILTER                                                                                                                                                                                                                                                                   
process.triggerSelectionLoneBunch = cms.EDFilter( "TriggerResultsFilter",
                                                   triggerConditions = cms.vstring('L1_AlwaysTrue'),
                                                   hltResults = cms.InputTag( "TriggerResults", "", "HLT" ),
                                                   l1tResults = cms.InputTag( "hltGtDigis" ),
                                                   l1tIgnoreMask = cms.bool( False ),
                                                   l1techIgnorePrescales = cms.bool( False ),
                                                   daqPartitions = cms.uint32( 1 ),
                                                   throw = cms.bool( True )
                                                   )

process.filter=cms.Sequence()
if(options.isSplash==1):
    process.filter+=process.spashesHltFilter
    process.ecalMultiFitUncalibRecHit.cpu.EBdigiCollection = cms.InputTag("ecalDigis", "ebDigis", "SPLASHFILTER1")#,'piZeroAnalysis')
    process.ecalMultiFitUncalibRecHit.cpu.EEdigiCollection = cms.InputTag("ecalDigis", "eeDigis", "SPLASHFILTER1")#,'piZeroAnalysis')

    #UNCALIB to CALIB
    process.filter += cms.Sequence( process.caloCosmicOrSplashRECOSequence
                                      * process.ecalMultiFitUncalibRecHit)
else:
    if(options.streamName=="AlCaP0"):
      if(options.loneBunch==1):
        process.filter+=process.triggerSelectionLoneBunch
      import RecoLocalCalo.EcalRecProducers.ecalMultiFitUncalibRecHit_cfi
      process.ecalMultiFitUncalibRecHit =  RecoLocalCalo.EcalRecProducers.ecalMultiFitUncalibRecHit_cfi.ecalMultiFitUncalibRecHit.clone()

      process.ecalMultiFitUncalibRecHit.EBdigiCollection = cms.InputTag('dummyHits','dummyBarrelDigisPi0')#,'piZeroAnalysis')
      process.ecalMultiFitUncalibRecHit.EEdigiCollection = cms.InputTag('dummyHits','dummyEndcapDigisPi0')#,'piZeroAnalysis')

      #UNCALIB to CALIB
      from RecoLocalCalo.EcalRecProducers.ecalRecHit_cfi import *
      process.ecalDetIdToBeRecovered =  RecoLocalCalo.EcalRecProducers.ecalDetIdToBeRecovered_cfi.ecalDetIdToBeRecovered.clone()
      process.ecalRecHit.killDeadChannels = cms.bool( False )
      process.ecalRecHit.recoverEBVFE = cms.bool( False )
      process.ecalRecHit.recoverEEVFE = cms.bool( False )
      process.ecalRecHit.recoverEBFE = cms.bool( False )
      process.ecalRecHit.recoverEEFE = cms.bool( False )
      process.ecalRecHit.recoverEEIsolatedChannels = cms.bool( False )
      process.ecalRecHit.recoverEBIsolatedChannels = cms.bool( False )

      process.reco_step = cms.Sequence(process.dummyHits
                                      * process.ecalMultiFitUncalibRecHit
                                      * process.ecalRecHit)
    else:
      #process.reco_step = cms.Sequence(process.reconstruction_step_multiFit)
      if(options.loneBunch==1):
        process.filter+=process.triggerSelectionLoneBunch
      process.reco_step = cms.Sequence(process.ecalLocalRecoSequenceAlCaStream)
      

### Process Full Path
if(options.isSplash==0):
    process.digiStep = cms.Sequence()



evtPlots = True if options.isSplash else False

if doAnalysis:
    process.load('EcalTiming.EcalTiming.ecalTimingCalibProducer_cfi')
    process.timing.DEBUG = cms.bool(options.debug)
    process.timing.timingCollection = cms.InputTag("EcalTimingEvents")
    process.timing.isSplash= cms.bool(True if options.isSplash else False)
    process.timing.saveTimingEvents= cms.bool(True)
    process.timing.makeEventPlots=evtPlots
    process.timing.globalOffset = cms.double(options.offset)
    process.timing.outputDumpFile = process.TFileService.fileName
    process.timing.energyThresholdOffsetEB = cms.double(options.minEnergyEB)
    process.timing.energyThresholdOffsetEE = cms.double(options.minEnergyEE)
    process.timing.storeEvents = cms.bool(True)
    process.analysis = cms.Sequence( process.timing)

process.load('EcalTiming.EcalTiming.EcalTimingSequence_cff')
process.seq = cms.Sequence()
if doReco:
    if options.isSplash:
        process.seq += cms.Sequence( process.filter * process.EcalTimingEventSeq )
    else:
        process.reco = cms.Sequence( (process.filter
                      + process.digiStep 
                      + process.reco_step)
                      * process.EcalTimingEventSeq
                      )
        process.seq += process.reco

if doAnalysis:
    process.seq += process.analysis

process.p = cms.Path(process.seq)
from datetime import datetime
processDumpFilename = "processDump" + datetime.now().strftime("%M%S%f") + ".py"
with open(processDumpFilename, 'w') as processDumpFile:
   processDumpFile.write(process.dumpPython())
