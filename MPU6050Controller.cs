using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// 透過 HTTP API 從樹莓派讀取 MPU6050 感測器數據並控制物件旋轉
/// </summary>
public class MPU6050Controller : MonoBehaviour
{
    [Header("API Settings")]
    [Tooltip("樹莓派的 IP 位址")]
    public string raspberryPiIP = "192.168.50.65";
    
    [Tooltip("API 端口")]
    public int port = 5000;
    
    [Tooltip("更新頻率（秒）")]
    public float updateInterval = 0.01f; // 100Hz
    
    [Header("Sensor Data")]
    public Vector3 accelerometer;
    public Vector3 gyroscope;
    public float temperature;
    
    [Header("Rotation Settings")]
    [Tooltip("是否啟用旋轉控制")]
    public bool enableRotation = true;
    
    [Tooltip("旋轉靈敏度")]
    public float rotationSensitivity = 1.0f;
    
    [Header("Debug")]
    public bool showDebugInfo = true;
    public string lastError = "";
    
    private string apiUrl;
    private bool isRequesting = false;
    private Quaternion targetRotation;
    
    // 數據結構對應 API 返回的 JSON
    [System.Serializable]
    private class MPU6050Response
    {
        public string status;
        public MPU6050Data data;
    }
    
    [System.Serializable]
    private class MPU6050Data
    {
        public AccelData accelerometer;
        public GyroData gyroscope;
        public float temperature;
        public float timestamp;
    }
    
    [System.Serializable]
    private class AccelData
    {
        public float x;
        public float y;
        public float z;
    }
    
    [System.Serializable]
    private class GyroData
    {
        public float x;
        public float y;
        public float z;
    }
    
    void Start()
    {
        // 構建 API URL
        apiUrl = $"http://{raspberryPiIP}:{port}/api/mpu6050";
        
        Debug.Log($"MPU6050 Controller 已啟動");
        Debug.Log($"連接到: {apiUrl}");
        
        // 開始持續請求數據
        StartCoroutine(RequestDataContinuously());
    }
    
    /// <summary>
    /// 持續請求 MPU6050 數據
    /// </summary>
    IEnumerator RequestDataContinuously()
    {
        while (true)
        {
            if (!isRequesting)
            {
                yield return StartCoroutine(GetMPU6050Data());
            }
            
            yield return new WaitForSeconds(updateInterval);
        }
    }
    
    /// <summary>
    /// 從 API 獲取 MPU6050 數據
    /// </summary>
    IEnumerator GetMPU6050Data()
    {
        isRequesting = true;
        
        using (UnityWebRequest request = UnityWebRequest.Get(apiUrl))
        {
            // 設置超時
            request.timeout = 2;
            
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    // 解析 JSON 數據
                    string json = request.downloadHandler.text;
                    MPU6050Response response = JsonUtility.FromJson<MPU6050Response>(json);
                    
                    if (response.status == "success")
                    {
                        // 更新感測器數據
                        accelerometer = new Vector3(
                            response.data.accelerometer.x,
                            response.data.accelerometer.y,
                            response.data.accelerometer.z
                        );
                        
                        gyroscope = new Vector3(
                            response.data.gyroscope.x,
                            response.data.gyroscope.y,
                            response.data.gyroscope.z
                        );
                        
                        temperature = response.data.temperature;
                        
                        // 根據感測器數據更新旋轉
                        if (enableRotation)
                        {
                            UpdateRotation();
                        }
                        
                        lastError = "";
                        
                        if (showDebugInfo)
                        {
                            Debug.Log($"Accel: {accelerometer}, Gyro: {gyroscope}, Temp: {temperature}°C");
                        }
                    }
                }
                catch (System.Exception e)
                {
                    lastError = $"JSON 解析錯誤: {e.Message}";
                    Debug.LogError(lastError);
                }
            }
            else
            {
                lastError = $"請求失敗: {request.error}";
                if (showDebugInfo)
                {
                    Debug.LogWarning(lastError);
                }
            }
        }
        
        isRequesting = false;
    }
    
    /// <summary>
    /// 根據加速度計數據更新物件旋轉
    /// </summary>
    void UpdateRotation()
    {
        // 使用加速度計計算傾斜角度
        // 注意：這是簡化版本，實際應用可能需要互補濾波器結合陀螺儀數據
        
        float roll = Mathf.Atan2(accelerometer.y, accelerometer.z) * Mathf.Rad2Deg;
        float pitch = Mathf.Atan2(-accelerometer.x, Mathf.Sqrt(accelerometer.y * accelerometer.y + accelerometer.z * accelerometer.z)) * Mathf.Rad2Deg;
        
        // 使用陀螺儀數據計算偏航（可選）
        float yaw = gyroscope.z * rotationSensitivity;
        
        // 應用旋轉
        targetRotation = Quaternion.Euler(pitch, yaw, roll);
        transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, Time.deltaTime * 5f);
    }
    
    void Update()
    {
        // 可以在這裡添加額外的更新邏輯
    }
    
    /// <summary>
    /// 測試連接
    /// </summary>
    public void TestConnection()
    {
        StartCoroutine(TestConnectionCoroutine());
    }
    
    IEnumerator TestConnectionCoroutine()
    {
        string statusUrl = $"http://{raspberryPiIP}:{port}/api/status";
        
        using (UnityWebRequest request = UnityWebRequest.Get(statusUrl))
        {
            yield return request.SendWebRequest();
            
            if (request.result == UnityWebRequest.Result.Success)
            {
                Debug.Log($"✅ 連接成功！");
                Debug.Log($"回應: {request.downloadHandler.text}");
            }
            else
            {
                Debug.LogError($"❌ 連接失敗: {request.error}");
            }
        }
    }
}
