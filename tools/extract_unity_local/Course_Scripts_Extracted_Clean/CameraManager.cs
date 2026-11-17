using UnityEngine;

public class CameraManager : MonoBehaviour
{
    InputManager inputManager;
    public Transform playerTransform;
    public Transform cameraPivot;
    private Vector3 camFollowVelocity = Vector3.zero;

    [Header("Camera Movement and Rotation")]
    public float camFollowSpeed = 0.05f;
    public float camLookSpeed = 2f;
    public float camPivotSpeed = 2f;
    public float lookAngle;
    public float pivotAngle;

    public float minimumPivotAngle = -35f;
    public float maximumPivotAngle = 60f;

    void Awake()
    {
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
        inputManager = FindObjectOfType<InputManager>();
        FindPlayerTarget();
    }

    private void LateUpdate()
    {
        HandleAllCameraMovement();
    }

    public void SetTarget(Transform newTarget)
    {
        playerTransform = newTarget;
    }

    public void FindPlayerTarget()
    {
        if (playerTransform != null) return;

        PlayerManager pm = FindObjectOfType<PlayerManager>();
        if (pm != null)
        {
            playerTransform = pm.transform;
            return;
        }

        GameObject playerTag = GameObject.FindWithTag("Player");
        if (playerTag != null)
        {
            playerTransform = playerTag.transform;
        }
    }

    public void HandleAllCameraMovement()
    {
        if (playerTransform == null)
        {
            FindPlayerTarget();
            if (playerTransform == null) return;
        }

        FollowTarget();
        RotateCamera();
    }

    void FollowTarget()
    {
        if (playerTransform == null) return;
        Vector3 targetPosition = Vector3.SmoothDamp(transform.position, playerTransform.position, ref camFollowVelocity, camFollowSpeed);
        transform.position = targetPosition;
    }

    private void RotateCamera()
    {
        if (inputManager == null) inputManager = FindObjectOfType<InputManager>();

        float inputX = Input.GetAxis("Mouse X");
        float inputY = Input.GetAxis("Mouse Y");

        if (inputManager != null && Mathf.Abs(inputManager.cameraInputX) > 0.001f)
        {
            inputX = inputManager.cameraInputX;
        }
        if (inputManager != null && Mathf.Abs(inputManager.cameraInputY) > 0.001f)
        {
            inputY = inputManager.cameraInputY;
        }

        lookAngle += (inputX * camLookSpeed * 50f * Time.deltaTime);
        pivotAngle -= (inputY * camPivotSpeed * 50f * Time.deltaTime);
        pivotAngle = Mathf.Clamp(pivotAngle, minimumPivotAngle, maximumPivotAngle);

        Vector3 rotation = Vector3.zero;
        rotation.y = lookAngle;
        Quaternion targetRotation = Quaternion.Euler(rotation);
        transform.rotation = targetRotation;

        if (cameraPivot != null)
        {
            rotation = Vector3.zero;
            rotation.x = pivotAngle;
            targetRotation = Quaternion.Euler(rotation);
            cameraPivot.localRotation = targetRotation;
        }
    }
}
