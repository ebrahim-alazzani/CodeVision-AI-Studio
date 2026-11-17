using UnityEngine;

public class CarController : MonoBehaviour
{
    public WheelCollider frontLeftWheel;
    public WheelCollider frontRightWheel;
    public WheelCollider rearLeftWheel;
    public WheelCollider rearRightWheel;

    public Transform frontLeftTransform;
    public Transform frontRightTransform;
    public Transform rearLeftTransform;
    public Transform rearRightTransform;

    public float maxSteerAngle = 30f;
    public float motorForce = 1500f;
    public float brakeForce = 3000f;

    private float horizontalInput;
    private float verticalInput;
    private bool isBraking;

    private void Update()
    {
        GetInput();
    }

    private void FixedUpdate()
    {
        HandleMotor();
        HandleSteering();
        UpdateWheels();
    }

    private void GetInput()
    {
        horizontalInput = Input.GetAxis("Horizontal");
        verticalInput = Input.GetAxis("Vertical");
        isBraking = Input.GetKey(KeyCode.Space);
    }

    private void HandleMotor()
    {
        frontLeftWheel.motorTorque = verticalInput * motorForce;
        frontRightWheel.motorTorque = verticalInput * motorForce;

        float currentBrakeForce = isBraking ? brakeForce : 0f;
        frontLeftWheel.brakeTorque = currentBrakeForce;
        frontRightWheel.brakeTorque = currentBrakeForce;
        rearLeftWheel.brakeTorque = currentBrakeForce;
        rearRightWheel.brakeTorque = currentBrakeForce;
    }

    private void HandleSteering()
    {
        float steerAngle = maxSteerAngle * horizontalInput;
        frontLeftWheel.steerAngle = steerAngle;
        frontRightWheel.steerAngle = steerAngle;
    }

    private void UpdateWheels()
    {
        UpdateSingleWheel(frontLeftWheel, frontLeftTransform);
        UpdateSingleWheel(frontRightWheel, frontRightTransform);
        UpdateSingleWheel(rearLeftWheel, rearLeftTransform);
        UpdateSingleWheel(rearRightWheel, rearRightTransform);
    }

    private void UpdateSingleWheel(WheelCollider collider, Transform transform)
    {
        Vector3 pos;
        Quaternion rot;
        collider.GetWorldPose(out pos, out rot);
        transform.position = pos;
        transform.rotation = rot;
    }
}
