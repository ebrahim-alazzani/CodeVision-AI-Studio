using UnityEngine;

public class MiniMapController : MonoBehaviour
{
    public Transform playerTransform;
    public float minimapHeight = 20f;

    private void LateUpdate()
    {
        if (playerTransform == null)
        {
            GameObject playerObj = GameObject.FindWithTag("Player");
            if (playerObj != null) playerTransform = playerObj.transform;
            return;
        }

        Vector3 newPos = playerTransform.position;
        newPos.y += minimapHeight;
        transform.position = newPos;

        transform.rotation = Quaternion.Euler(90f, playerTransform.eulerAngles.y, 0f);
    }
}
