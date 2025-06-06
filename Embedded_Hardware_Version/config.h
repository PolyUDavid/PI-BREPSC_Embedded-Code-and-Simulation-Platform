#ifndef CONFIG_H
#define CONFIG_H

// RSU settings
#define DEFAULT_TX_POWER_DBM -10
#define RSSI_WAITING_THRESHOLD_DBM -70

// Pedestrian settings
#define PEDESTRIAN_RADIUS 10
#define STATIONARY_THRESHOLD_FRAMES_SHORT 60
#define STATIONARY_THRESHOLD_FRAMES_LONG 180

// Traffic Light Timings (in frames)
#define MIN_VEHICLE_GREEN_TIME 300
#define VEHICLE_YELLOW_TIME 120
#define PEDESTRIAN_WALK_TIME 420
#define PEDESTRIAN_FLASH_TIME 180
#define ALL_RED_TIME 60

#endif