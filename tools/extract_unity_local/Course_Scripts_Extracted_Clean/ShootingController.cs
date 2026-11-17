using UnityEngine;

public class ShootingController : MonoBehaviour
{
    public Camera mainCamera;
    public Transform firePoint;
    public GameObject bulletImpactPrefab;
    public float fireRate = 0.15f;
    public float damage = 25f;
    public float range = 100f;

    private float nextFireTime = 0f;
    public bool isAiming = false;

    private void Update()
    {
        if (Input.GetButton("Fire2"))
        {
            isAiming = true;
        }
        else
        {
            isAiming = false;
        }

        if (Input.GetButton("Fire1") && Time.time >= nextFireTime)
        {
            nextFireTime = Time.time + fireRate;
            Shoot();
        }
    }

    private void Shoot()
    {
        RaycastHit hit;
        Vector3 rayOrigin = mainCamera != null ? mainCamera.transform.position : transform.position;
        Vector3 rayDir = mainCamera != null ? mainCamera.transform.forward : transform.forward;

        if (Physics.Raycast(rayOrigin, rayDir, out hit, range))
        {
            if (bulletImpactPrefab != null)
            {
                Instantiate(bulletImpactPrefab, hit.point, Quaternion.LookRotation(hit.normal));
            }

            PoliceOfficer police = hit.collider.GetComponent<PoliceOfficer>();
            if (police != null)
            {
                police.TakeDamage(damage);
            }
        }
    }
}
