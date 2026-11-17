using UnityEngine;

namespace GTAViceCityClone.Vehicles
{
    /// <summary>
    /// CarController handles wheel collider physics, engine torque, steering angles, and wheel mesh visual transforms.
    /// Reconstructed cleanly from Episodes 38, 72, 74.
    /// </summary>
    public class CarController : MonoBehaviour
    {
        [Header("Wheel Colliders")]
        public WheelCollider frontLeftWheel;
        public WheelCollider frontRightWheel;
        public WheelCollider rearLeftWheel;
        public WheelCollider rearRightWheel;

        [Header("Wheel Visual Meshes")]
        public Transform frontLeftMesh;
        public Transform frontRightMesh;
        public Transform rearLeftMesh;
        public Transform rearRightMesh;

        [Header("Car Driving Parameters")]
        public float maxMotorTorque = 600f;
        public float maxSteeringAngle = 30f;
        public float brakeTorque = 3000f;
        public float currentSpeed; // in km/h

        [Header("Current Inputs")]
        public float horizontalInput;
        public float verticalInput;
        public bool isBraking;

        [Header("Center of Mass")]
        public Vector3 centerOfMassOffset = new Vector3(0f, -0.5f, 0f);
        private Rigidbody carRigidbody;

        private void Start()
        {
            carRigidbody = GetComponent<Rigidbody>();
            if (carRigidbody != null)
            {
                carRigidbody.centerOfMass += centerOfMassOffset;
            }
        }

        private void FixedUpdate()
        {
            GetInputs();
            HandleMotor();
            HandleSteering();
            HandleBraking();
            UpdateWheels();

            if (carRigidbody != null)
            {
                currentSpeed = carRigidbody.linearVelocity.magnitude * 3.6f;
            }
        }

        private void GetInputs()
        {
            // Keyboard inputs (if not driven by mobile UI)
            if (horizontalInput == 0f && verticalInput == 0f && !isBraking)
            {
                horizontalInput = Input.GetAxis("Horizontal");
                verticalInput = Input.GetAxis("Vertical");
                isBraking = Input.GetKey(KeyCode.Space);
            }
        }

        private void HandleMotor()
        {
            float torque = verticalInput * maxMotorTorque;

            // Rear-wheel drive
            if (rearLeftWheel != null) rearLeftWheel.motorTorque = torque;
            if (rearRightWheel != null) rearRightWheel.motorTorque = torque;
        }

        private void HandleSteering()
        {
            float currentSteerAngle = horizontalInput * maxSteeringAngle;

            if (frontLeftWheel != null) frontLeftWheel.steerAngle = currentSteerAngle;
            if (frontRightWheel != null) frontRightWheel.steerAngle = currentSteerAngle;
        }

        private void HandleBraking()
        {
            float currentBrake = isBraking ? brakeTorque : 0f;

            if (frontLeftWheel != null) frontLeftWheel.brakeTorque = currentBrake;
            if (frontRightWheel != null) frontRightWheel.brakeTorque = currentBrake;
            if (rearLeftWheel != null) rearLeftWheel.brakeTorque = currentBrake;
            if (rearRightWheel != null) rearRightWheel.brakeTorque = currentBrake;
        }

        private void UpdateWheels()
        {
            UpdateSingleWheel(frontLeftWheel, frontLeftMesh);
            UpdateSingleWheel(frontRightWheel, frontRightMesh);
            UpdateSingleWheel(rearLeftWheel, rearLeftMesh);
            UpdateSingleWheel(rearRightWheel, rearRightMesh);
        }

        private void UpdateSingleWheel(WheelCollider wheelCollider, Transform wheelMesh)
        {
            if (wheelCollider == null || wheelMesh == null) return;

            Vector3 pos;
            Quaternion rot;
            wheelCollider.GetWorldPose(out pos, out rot);

            wheelMesh.position = pos;
            wheelMesh.rotation = rot;
        }

        #region Mobile Driving UI Callbacks
        public void SetMobileInputs(float h, float v, bool brake)
        {
            horizontalInput = h;
            verticalInput = v;
            isBraking = brake;
        }

        public void OnGasButtonDown() => verticalInput = 1f;
        public void OnGasButtonUp() => verticalInput = 0f;
        public void OnReverseButtonDown() => verticalInput = -1f;
        public void OnReverseButtonUp() => verticalInput = 0f;
        public void OnSteerLeftDown() => horizontalInput = -1f;
        public void OnSteerLeftUp() => horizontalInput = 0f;
        public void OnSteerRightDown() => horizontalInput = 1f;
        public void OnSteerRightUp() => horizontalInput = 0f;
        public void OnBrakeButtonDown() => isBraking = true;
        public void OnBrakeButtonUp() => isBraking = false;
        #endregion
    }
}
