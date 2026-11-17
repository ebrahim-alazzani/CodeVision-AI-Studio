using UnityEngine;

public class CarCameraController : MonoBehaviour
{
    public Transform targetCar;
    public float distance = 6.0f;
    public float height = 2.5f;
    public float rotationDamping = 3.0f;
    public float heightDamping = 2.0f;

    private void LateUpdate()
    {
        if (targetCar == null) return;

        float wantedRotationAngle = targetCar.eulerAngles.y;
        float wantedHeight = targetCar.position.y + height;

        float currentRotationAngle = transform.eulerAngles.y;
        float currentHeight = transform.position.y;

        currentRotationAngle = Mathf.LerpAngle(currentRotationAngle, wantedRotationAngle, rotationDamping * Time.deltaTime);
        currentHeight = Mathf.Lerp(currentHeight, wantedHeight, heightDamping * Time.deltaTime);

        Quaternion currentRotation = Quaternion.Euler(0, currentRotationAngle, 0);

        transform.position = targetCar.position;
        transform.position -= currentRotation * Vector3.forward * distance;

        Vector3 tempPos = transform.position;
        tempPos.y = currentHeight;
        transform.position = tempPos;

        transform.LookAt(targetCar.position + Vector3.up * 1.2f);
    }
}
