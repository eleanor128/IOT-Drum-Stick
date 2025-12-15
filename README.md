# IOT Drum Set
This is a personal project in IM5032 - Practical Internet of Things.  
Drums are not like guitar which can be easily portable, and the exsisting air drumstick is pretty expensive, so this project aims to implement an easy air drumstick using **Rasberry Pi4** and **mpu6050 sensor**.


<div align="center">
  <img src="readme_img/image.png" alt="IOT Drum Set" width="100%">
  <img src="readme_img/full.jpg" alt="IOT Drum Set" width="100%">
  <!-- <img src="readme_img/close.jpg" alt="IOT Drum Set" width="100%"> -->
</div>


## Required Components
| Item | Quantity | Purpose |
|-----|----------|---------|
| Raspberry Pi 4  | 1 | Main controller for data processing and system control |
| MPU6050  | 2 | Detect drumstick motion |
| Drumstick | 2 | Otherwise it can't be an air drumstick : ) |
| Breadboard | 1 | For better wiring |
| Jumper wires  | many | Connect MPU6050 to Raspberry Pi GPIO |
| Tape  | many | Make everything neat |

## Circuit Diagram
<div align="center">
  <img src="readme_img/Wiring.jpg" alt="IOT Drum Set" width="100%">
</div>


## Getting Start
### 1. Environment Setup


---

### 2. MPU6050 Sensor Setup

This section explains how to connect **one or two MPU6050 sensors** to a Raspberry Pi.

The MPU6050 is a 6-axis IMU sensor (3-axis accelerometer + 3-axis gyroscope), which can detect movement and rotation in all directions.  
It is important to understand the relationship between the sensor axes and real-world directions, as this directly affects motion interpretation.

<div align="center" style="display: flex; gap: 10px;">
  <img src="readme_img/mpu6050.png" alt="MPU6050 module" width="50%">
  <img src="readme_img/mpu6050_axis.png" alt="MPU6050 axis orientation" width="50%">
</div>

<br>
<br>

#### Enable I2C Interface

First, open the Raspberry Pi configuration tool and enable **I2C** and **SPI**:

<img src="readme_img/setting.png" alt="I2C detection result" width="100%">

#### Install I2C Tools and Detect Sensor

Install I2C tools:

    sudo apt-get install i2c-tools

Check whether the Raspberry Pi can detect the sensor:

    i2cdetect -y 1

If your Raspberry Pi uses a different I2C bus, try:

    i2cdetect -y 0

If `0x68` or `0x69` appears as shown below, the sensor is successfully detected.

<img src="readme_img/I2C.png" alt="I2C detection result" width="100%">

#### Connecting One MPU6050 Sensor

By default, the MPU6050 uses I2C address `0x68`.

| MPU6050 | Raspberry Pi |
|--------|--------------|
| VCC    | 3.3V / 5V    |
| GND    | GND          |
| SDA    | SDA (GPIO 2) |
| SCL    | SCL (GPIO 3) |
| AD0    | GND          |

After wiring, run `i2cdetect -y 1`.  If `0x68` appears, the sensor is connected correctly.

#### Connecting Two MPU6050 Sensors

To connect two MPU6050 sensors on the same I2C bus, their I2C addresses must be different.

- Sensor 1: `AD0 → GND` → Address `0x68`
- Sensor 2: `AD0 → VCC` → Address `0x69`

Both sensors share the same SDA and SCL lines.

| Signal | Sensor 1 | Sensor 2 | Raspberry Pi |
|--------|----------|----------|--------------|
| VCC    | VCC      | VCC      | 3.3V / 5V    |
| GND    | GND      | GND      | GND          |
| SDA    | SDA      | SDA      | GPIO 2       |
| SCL    | SCL      | SCL      | GPIO 3       |
| AD0    | GND      | VCC      | —            |

After wiring, run `i2cdetect -y 1`.
You should see **both `0x68` and `0x69`**, indicating that two sensors are detected successfully.

You can also refer to the following tutorial for more details:  [https://atceiling.blogspot.com/2017/02/raspberry-pi-mpu-6050.html](https://atceiling.blogspot.com/2017/02/raspberry-pi-mpu-6050.html)




### 3. Calitrate Sensor Data
The offset values were obtained by collecting data while the sensors were **stationary and flat** on a table, then calculating the average error over multiple samples.

**Method:**

1. **Place the sensor flat on a stable surface** (drumstick lying horizontally on a table)

2. **Run the test script**  `mpu6050_test.py` to collect raw data. This script will record 100-200 samples of raw accelerometer and gyroscope readings while stationary

3. **Calculate  the average values** and the offest values of each sensor will be updated and used in `calibration_right.py` and `calibration_left.py`


### 4. 3D World Setup

The following figure illustrates the setup of the 3D world and the mapping between the sensor directions and the virtual drum set.

<img src="readme_img/3D_settings.jpg" alt="3D world and axis mapping" width="100%">

This project uses **Three.js** (https://threejs.org/) to create the invironment and the virtual drum set.  
Due to time limitations, the bass drum is not included in the current implementation. 

To simplify motion interpretation, it would have been easier to predefine the axis mapping between the MPU6050 sensor and the 3D world.  
Be careful, the coordinate system of the 3D world is fixed and does **not change with the camera position**.

From the user’s point of view, the relation of each data is as follows:

| Movement | 3D World Mapping | Sensor Data |
|---------|------------------|-------------|
| Left–Right Movement | X-axis | Yaw (rotation around Z-axis) |
| Up–Down Movement | Y-axis | Pitch (rotation around Y-axis) |
| Forward–Backward Movement | Z-axis | Pitch (rotation around Y-axis) + ax (X-axis acceleration) |
| Vertical Drumstick Swing (Hitting)| rotation x | Pitch (rotation around Y-axis) + gy (Y-axis angular velocity) |
| Horizontal Drumstick Swing | rotation y | Yaw (rotation around Z-axis) |





### 9. Failed Attempts

#### spleeter to split drum sound form songs

#### Hitting Zone optimization 


### References
