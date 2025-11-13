import mpu6050  # 這是第三方套件，名稱不變
import time

# Create a new Mpu6050 object
sensor = mpu6050.mpu6050(0x68)  # 改用 sensor 變數名稱避免混淆

# Define a function to read the sensor data
def read_sensor_data():
    # Read the accelerometer values
    accelerometer_data = sensor.get_accel_data()

    # Read the gyroscope values
    gyroscope_data = sensor.get_gyro_data()

    # Read temp
    temperature = sensor.get_temp()

    return accelerometer_data, gyroscope_data, temperature

# Start a while loop to continuously read the sensor data
while True:

    # Read the sensor data
    accelerometer_data, gyroscope_data, temperature = read_sensor_data()

    # Print the sensor data
    print("Accelerometer data:", accelerometer_data)
    print("Gyroscope data:", gyroscope_data)
    print("Temp:", temperature)

    # Wait for 1 second
    time.sleep(1)