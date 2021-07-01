#include "LeaderCouzin.h"

#include <map>
#include <vector>

#include <opencv2/opencv.hpp>

#include "controller/IController.h"
#include "controller/movement/IMovement.h"
#include "controller/movement/NaturalMovement.h"
#include "controller/TwoWheelsController.h"

#include <stdio.h>
#include <time.h>

//#include <thread>
//#include <chrono>

#include <windows.h> 
#include <stdio.h>

#include "core/RoboAgent.h"


// Visualization
const int DbgImgScale = 6;
const cv::Scalar BACKGROUND_COLOUR = CV_RGB(0, 0, 0);
const cv::Scalar ROBOFISH_COLOUR = CV_RGB(255, 255, 255);
const cv::Scalar FISH_COLOUR = CV_RGB(100, 100, 100);
const cv::Scalar NEAREST_NEIGHBOUR_COLOUR = CV_RGB(255, 0, 0);
const cv::Scalar CLUSTER_CENTER_COLOUR = CV_RGB(0, 180, 0);
const cv::Scalar HULL_COLOUR = CV_RGB(70, 70, 70);
const cv::Scalar TEXT_COLOUR = CV_RGB(30, 150, 30);
const cv::Scalar TARGET_PT_COLOUR = CV_RGB(100, 100, 255);
const cv::Scalar ZONE_COLOUR = CV_RGB(120, 120, 120);
const std::string DbgWindow = "LeaderCouzin";

// Target point distance
const double TargetDist = 6.0;

cv::Point LeaderCouzin::_cmToDbgImgPx(cv::Point2f point_cm)
{
	int x = DbgImgScale * point_cm.x;
	int y = _dbgImgHeight_px - DbgImgScale * point_cm.y;
	return cv::Point(x, y);
}

LeaderCouzin::LeaderCouzin(const FishTank& tank) :
	_tank(&tank),
	_dbgImage(NULL),
	_vis(false),
	_zone(0),
	_checkTime(0),
	_stateSeconds(0),
	_nearestNeighbourID(-1)

{
	//getting area size information from fish tank and use it for arena and image size
	double arenaWidth_cm = _tank->areaWidth_cm();
	double arenaHeight_cm = _tank->areaHeight_cm();
	_dbgImgWidth_px = arenaWidth_cm * DbgImgScale;
	_dbgImgHeight_px = arenaHeight_cm * DbgImgScale;
	_posToReach = cv::Point2f(-1,-1);
	_thisTime = clock();
	_lastTime = _thisTime;
	_timeCounter = 0;
	_stateTimer = clock();
	_stateTimeDiff = _stateTimer;
	_state = 'F';
	_stateUnchanged = true;
}

LeaderCouzin::~LeaderCouzin(void)
{
}

void LeaderCouzin::init()
{
	set(LEADING_MODE,BehaviourParamInteger(0));
	set(ROBO_REJECTION_ZONE,BehaviourParamDouble(1.0));
	set(ROBO_COMFORT_ZONE,BehaviourParamDouble(8.0));
	set(FISH_REJECTION_ZONE,BehaviourParamDouble(1.0));
	set(FISH_COMFORT_ZONE,BehaviourParamDouble(8.0));
	set(IS_PAUSED,BehaviourParamInteger(0));
}

int LeaderCouzin::lookForNearestNeighbour(const IPose& curPose)
{
	double min = std::numeric_limits<double>::infinity();
	int id;

	for(int i = 0; i < _fishPoses.size(); i++)
	{
		double dist = CvHelper::getDistance(curPose.position_cm(), _fishPoses.at(i).position_cm());
		if(min > dist)
		{
			min = dist;
			id = i;
		}
	}

	return id;
}

//in helper
bool LeaderCouzin::cvPointSmallerThanX(cv::Point2f a, float x)
{
	if(a.x < x && a.y < x)
		return true;

	return false;
}
//in helper
bool LeaderCouzin::almostEqual(cv::Point2f a, cv::Point2f b)
{
	if(a == b)
		return true;

	cv::Point2f c = a-b;
	cv::Point2f absoluteError; 
	absoluteError.x = std::abs(c.x);
	absoluteError.y = std::abs(c.y);

	if (cvPointSmallerThanX(absoluteError, 2) == true)
		return true;

	return false;
}


MotorSpeeds LeaderCouzin::nextSpeeds(const IPose& curPose, IMovement& move, IController& controller)
{
	_fishPoses = _tank->fishPoses();
	
	// If roboter still has no nearest neighbour look for one.
	if(_nearestNeighbourID == -1)
		_nearestNeighbourID = lookForNearestNeighbour(curPose);

	// Next target for roboter
	std::deque<cv::Point2f> nextPoint;

	_nearestNeighbour = _fishPoses.at(_nearestNeighbourID);

	// Indicates the condition for the next transition between states
	char transition;

	
	_relativePosition = positionController.controlPositionToFish();

	
		if(almostEqual( _posToReach, curPose.position_cm()))
		{
			_state = _maTest.executeStateMachine('e');
			_posToReach = cv::Point2f(-1,-1);
			std::cout << "Should change to FOllowing! \n";
		}
		
	// Timer for following time in comfort zone before roboter is switching to leading mode
	_thisTime = clock();
	_timeCounter += (double)(_thisTime - _lastTime);
	_checkTime = (_timeCounter/CLOCKS_PER_SEC);
	_lastTime = _thisTime;

	_roboterComfortZoneRadius = get(ROBO_REJECTION_ZONE).value<double>() + get(ROBO_COMFORT_ZONE).value<double>();
	_roboterAttractionZoneRadius = _roboterComfortZoneRadius + 100;

	//enum verwenden, siehe header
	std::string zone;

	double distanceRoboterNearestNeighbour = CvHelper::getDistance(curPose.position_cm(), _fishPoses.at(_nearestNeighbourID).position_cm());
	if(distanceRoboterNearestNeighbour > _roboterComfortZoneRadius && distanceRoboterNearestNeighbour > _roboterRejectionZoneRadius)
		zone = "attraction";
	if(distanceRoboterNearestNeighbour < _roboterComfortZoneRadius && distanceRoboterNearestNeighbour > _roboterRejectionZoneRadius)
		zone = "comfort";

	_relativePosition.x = - _relativePosition.x;
	_relativePosition.y = - _relativePosition.y;
	cv::Point2f target = positionController.rotatePointAroundTarget(_relativePosition, _nearestNeighbour);

	target = checkRejection(curPose, target);

	
	
	if(zone == "comfort")
	{
		target = comfort(curPose, controller);
		//std::cout << "Robo in Comfort zone!!!!!!!!!!!!!1 \n";
	}
	
	if(zone == "attraction")
	{
		attraction(curPose, controller);
	}

	_tar = target;

	if(_posToReach != cv::Point2f(-1,-1))
		nextPoint.push_back(_posToReach);
	else 
		nextPoint.push_back(target);

	
	visualizationProcess(curPose);


	//enum movement type
	//Umschreiben, sodass kleiner
	// if behavior is paused via GUI checkbox
	// return zero motor speeds
	if( get(LeaderCouzin::ATTRIBUTE::IS_PAUSED).value<int>() != 0 ) //pause in probs einbinden und hier verwenden
	{
		return  MotorSpeeds (0,0);
	}


		if ( zone == "attraction" ) //enum verwenden für zonenbenennung
		{
			switch (ATTRACTION) // ToDo: couzin mit ou! move info for attraction einfügen
			{
			case 0:
				emit sendMovement(0);
				/*
				//motorSpeed = direct.speeds(curPose, nextPoint, controller);
				//static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_fasterspeed);
				//static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationAttractionSpeed);
				*/
				break;
			case 1:
				emit sendMovement(1);
				/*
				//motorSpeed= natural.speeds(curPose, nextPoint, controller);
				*/
				break;
			default:
				emit sendMovement(0);
				/*
				//motorSpeed = direct.speeds(curPose, nextPoint, controller);
				//static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_fasterspeed);
				//static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationAttractionSpeed);
				*/
				break;
			}
		}

		if( zone == "comfort" && _state != 'L' )
		{
			switch (COMFORT) //move info comfort einfügen
			{
			case 0:
				emit sendMovement(1);//motorSpeed= natural.speeds(curPose, nextPoint, controller);
				break;
			case 1:
				emit sendMovement(0);//motorSpeed = direct.speeds(curPose, nextPoint, controller);
				//static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_slowspeed);
				//static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationComfortSpeed);
				break;
			default:
				emit sendMovement(1);//motorSpeed= natural.speeds(curPose, nextPoint, controller);
				break;
			}
		}

		if ( zone == "comfort" && _state == 'L' )
		{
			switch (LEADING) //move info wenn in leading mode einfügen
			{
			case 0:
				emit sendMovement(0);//motorSpeed = direct.speeds(curPose, nextPoint, controller);
				//static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_fasterspeed);
				//static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationAttractionSpeed);
				break;
			case 1:
				emit sendMovement(1);//motorSpeed= natural.speeds(curPose, nextPoint, controller);
				break;
			default:
				emit sendMovement(0);//motorSpeed = direct.speeds(curPose, nextPoint, controller);
				//static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_fasterspeed);
				//static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationAttractionSpeed);
				break;
			}

		}
		
		
		//return motorSpeed;
		return move.speeds(curPose, nextPoint, controller);
	
}

void LeaderCouzin::attraction(const IPose& curPose, IController& controller)
{
	/*static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_fasterspeed);
	static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationAttractionSpeed);*/
	//TODO Movementset for Attraction
	
	cv::Point2f target;
		_checkTime = 0;
		_timeCounter = 0;

		if(_state == 'L')
			_state = _maTest.executeStateMachine('c');

		//return target = (_fishPoses.at(_nearestNeighbourID).position_cm());
}

cv::Point2f LeaderCouzin::comfort(const IPose& curPose, IController& controller)
{


		if(_latencyDelay > 0 && _state != 'L')
	{
		int latencyDelay = rand() % _latencyDelay;
		Sleep(latencyDelay);
	}

	///////////////////////////////////////////// Comfort zone, leader behaviour
	/*if(_state != 'L')
		Sleep(_latencyDelay);*/



	//TODO von GUI aus steuerbar
		if(int _checkRand = 0 && _state == 'F') //rand in probs einfügen und hier verwenden (int an aus)
	{
		// Timer for state change if random mode is possible. 
		_stateTimer = clock();
		_stateSeconds += ((double)(_stateTimer-_stateTimeDiff)/CLOCKS_PER_SEC);
		_stateTimeDiff = _stateTimer;

		_random = 5;//rand() % 3 + 3;

		if(_stateSeconds > _random)
		{
			_state = _maTest.executeStateMachine('a'); 
			_stateSeconds = 0;
			_stateUnchanged = false;
		}
		else
			_stateUnchanged = true;

		if(_state == 'R')
		{
		cv::Point2f	nextPoint = randomMode(curPose);
		return nextPoint;
		}
	}



	/*static_cast<TwoWheelsController&>(controller).setMaxFwdCtrlSpeed(_slowspeed);
	static_cast<TwoWheelsController&>(controller).setMaxTurnCtrlSpeed(_orientationComfortSpeed);*/
	//TODO Movementset vor Leading and Following

	cv::Point2f target;

	double distanceRoboterNearestNeighbour = CvHelper::getDistance(curPose.position_cm(), _fishPoses.at(_nearestNeighbourID).position_cm());

	int _dwellTime = 0; //in probs einfügen und ersetzen
	//a) schwimm direkt zum zielpunkt tankmitte,
	if( distanceRoboterNearestNeighbour < _roboterComfortZoneRadius && _leadingMode == 0 && _checkTime >= _dwellTime && _state != 'R')
	{
		_state = _maTest.executeStateMachine('b'); 
		cv::Point2f tankcenter(40,40);
		target = tankcenter;
	}
	else if(distanceRoboterNearestNeighbour < _roboterComfortZoneRadius && _leadingMode == 0 && _checkTime < _dwellTime && _state != 'R')
	{
		return _tar;
	}


	/*b) align und schwimm mit bestimmten Winkel weg, auf einen fisch (nn) heruntergebrochen

	**  align with them according to Couzin2002, eqns (2) and (3) and 
	following paragraph.
	**  d(t + tau) = .5 (d_o(t + tau) + d_a(t + tau)), or d_o [d_a] if 
	_roboterAttractionZone [_roboterComfortZone] is empty
	*/

	if( distanceRoboterNearestNeighbour < _roboterComfortZoneRadius && _leadingMode == 1 && _checkTime > _dwellTime && _state != 'R')
	{
		cv::Vec2f oriDir;

		int _blindAngle2 =0;
		double ori_rad = _fishPoses.at(_nearestNeighbourID).orientation_rad();
		cv::Vec2f fishDir(cos(ori_rad), sin(ori_rad));
		oriDir += fishDir; //Default, senden an gui;
		cv::Vec2f presentDir(cos(_blindAngle2), sin(_blindAngle2)); //wert von gui //TODO: Winkel überprüfen!!! Ob Grad oder Deg!
		//angestrebte richtung
		presentDir = TargetDist * cv::normalize(presentDir); //original nur oriDir

		_state = _maTest.executeStateMachine('b');
		cv::Vec2f curPosVec = curPose.position_cm();
		target = (curPosVec + presentDir);		
	}
	else if(distanceRoboterNearestNeighbour < _roboterComfortZoneRadius && _leadingMode == 1 && _checkTime <= _dwellTime && _state != 'R')
	{
		if(_checkTime <= _dwellTime)//TODO check if unnötig
		{
			target = (_fishPoses.at(_nearestNeighbourID).position_cm());
		}
	}

	return target;
}

cv::Point2f LeaderCouzin::checkRejection(const IPose& curPose, cv::Point2f target)
{
	
	int roboterRejectionZoneCount = 0;       // # of fish in rejection zone (_roboterRejectionZone)

	//da nur eine zone, einfachere datenstruktur?
	enum Zone
	{
		Rejection,
	};

	std::map<FishPose, Zone> zones;

	int robotFishID = -1;

	_fishPoses = _tank->fishPoses();
	std::vector<FishPose>::const_iterator fish_it;

	for (fish_it = _fishPoses.begin();
		fish_it != _fishPoses.end(); ++fish_it)
	{
		double dist = CvHelper::getDistance(curPose.position_cm(), fish_it->position_cm());

		if (dist < _roboterRejectionZoneRadius)
		{
			zones[*fish_it] = Rejection;
			++roboterRejectionZoneCount;
		}
	}


	///////////////////////////////////////////// Rejection zone, repulsive behaviour

	/** Rule 1, highest priority:
	**  If there are fish in the zone of rejection, move away from them.
	**  d(t + tau) = d_r(t + tau)
	**/
	//sollte übernehmbar sein, heißt rejectionzone doch counten
	if (roboterRejectionZoneCount > 0)
	{
		std::cout << "Roboter in rejection zone \n";
		// calculate d_r(t + tau) -- see Couzin2002, eqn (1)
		cv::Vec2f rejDir;

		// for each j != r in _roboterRejectionZone: add summand to d_r
		for (std::map<FishPose, Zone>::const_iterator fishZone_it = zones.begin();
			fishZone_it != zones.end(); ++fishZone_it)
		{
			if (fishZone_it->second == Rejection
				&& fishZone_it->first.fishID() != robotFishID) // !! TODO: based on position?
			{
				// subtract unit vector "robot -> fish"
				cv::Vec2f roboToFish = fishZone_it->first.position_cm() - curPose.position_cm();
				rejDir -= cv::normalize(roboToFish);
			}
		}

		cv::Vec2f curPosVec = curPose.position_cm();

		target = curPosVec + TargetDist * cv::normalize(rejDir);
		
		////nextPoint.push_back(target);
		//qDebug()/*myfile*/ << "C2D.  " << roboterRejectionZoneCount << " fish in _roboterRejectionZone, driving to ("
		//	<< nextPoint[0].x << ", " << nextPoint[0].y << ") \n";

	}


		return target;
}

cv::Point2f LeaderCouzin::randomMode (const IPose& curPose)
{

	if(_latencyDelay > 0)
	{
		int latencyDelay = rand() % _latencyDelay;
		Sleep(latencyDelay);
	}
	
	if(_posToReach == cv::Point2f(-1,-1))
	{
		int a = rand() % 5;
		int b = rand() % 2;
		cv::Point2f randomPoint(a,b);
		randomPoint ;//include when outsource done = rotatePointAroundTarget(randomPoint,_nearestNeighbour);
		_posToReach = randomPoint;
		return _posToReach;
	}

}





void LeaderCouzin::visualizationProcess(const IPose& curPose)
{
	if(_vis == false)
		return;

	*_dbgImage = BACKGROUND_COLOUR;

	// Draw robot position
	cv::Point robotInDbgImg = _cmToDbgImgPx(curPose.position_cm());
	cv::circle(*_dbgImage, robotInDbgImg, 2, ROBOFISH_COLOUR, CV_FILLED);
	cv::circle(*_dbgImage, robotInDbgImg, 4, ROBOFISH_COLOUR);

	// Draw zones of roboter
	cv::circle(*_dbgImage, robotInDbgImg,
		DbgImgScale * _roboterRejectionZoneRadius, ZONE_COLOUR);
	cv::circle(*_dbgImage, robotInDbgImg,
		DbgImgScale * _roboterComfortZoneRadius, ZONE_COLOUR);
	//cv::circle(*_dbgImage, robotInDbgImg, DbgImgScale * _roboterAttractionZoneRadius, ZONE_COLOUR);

	//draw fish zone of nn?

	//Robo target point, testing only, remove later
	_tar = _cmToDbgImgPx(_tar);
	cv::circle(*_dbgImage, _tar, 2, cv::Scalar(0, 255,255), CV_FILLED);
	
	cv::Point2f posToReach = _cmToDbgImgPx(_posToReach);
	cv::circle(*_dbgImage, posToReach, 2, cv::Scalar(255, 0 ,0), CV_FILLED);


	for (int i = 0; i < _fishPoses.size(); i++)
	{

		if(i == _nearestNeighbourID)
		{
			cv::Point posInDbgImg = _cmToDbgImgPx(_fishPoses.at(i).position_cm());
			cv::circle(*_dbgImage, posInDbgImg, 2, NEAREST_NEIGHBOUR_COLOUR, CV_FILLED);
		}
		else
		{
			cv::Point posInDbgImg = _cmToDbgImgPx(_fishPoses.at(i).position_cm());
			cv::circle(*_dbgImage, posInDbgImg, 2, FISH_COLOUR, CV_FILLED);
		}

	}

	cv::imshow(DbgWindow, *_dbgImage);

}

void LeaderCouzin::visualize(bool on)
{
	if (on)
	{
		_vis = true;
		_dbgImage = new cv::Mat(_dbgImgHeight_px, _dbgImgWidth_px, CV_8UC3, BACKGROUND_COLOUR);

		cv::namedWindow(DbgWindow);
		cv::imshow(DbgWindow, *_dbgImage);
	}
	else 
	{
		_vis = false;
		cv::destroyAllWindows();
		delete _dbgImage;
	}
}