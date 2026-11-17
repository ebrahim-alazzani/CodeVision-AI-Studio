using System.Collections;
using UnityEngine;
using GTAViceCityClone.Player;
using GTAViceCityClone.AI;
using GTAViceCityClone.Police;

namespace GTAViceCityClone.Shooting
{
    /// <summary>
    /// ShootingController manages raycast shooting, damage calculation, ammo/reloading, muzzle flash, and weapon inventory switching.
    /// Reconstructed cleanly from Episodes 30, 31, 32, 33, 46, 47, 48, 60, 62, 71, 73.
    /// </summary>
    public class ShootingController : MonoBehaviour
    {
        [Header("Script References")]
        [SerializeField] private InputManager inputManager;
        [SerializeField] private AnimatorManager animatorManager;
        [SerializeField] private Camera mainCamera;

        [Header("Weapon Stats")]
        public float giveDamageOf = 25f;
        public float fireRange = 100f;
        public float fireRate = 5f;
        private float nextTimeToFire = 0f;

        [Header("Ammo & Reloading")]
        public int magazineCapacity = 30;
        public int maxAmmo = 180;
        public int currentMagazine;
        public int currentAmmo;
        public float reloadTime = 2f;
        public bool isReloading = false;

        [Header("Visual Effects")]
        public Transform firePoint;
        public ParticleSystem muzzleFlash;
        public GameObject fleshImpactPrefab;
        public GameObject metalImpactPrefab;
        public GameObject defaultImpactPrefab;

        [Header("Weapon Inventory Slots")]
        public GameObject[] weaponSlots;
        public int currentWeaponIndex = 0;

        private void Awake()
        {
            inputManager = GetComponent<InputManager>();
            animatorManager = GetComponent<AnimatorManager>();

            if (mainCamera == null)
            {
                mainCamera = Camera.main;
            }
        }

        private void Start()
        {
            currentMagazine = magazineCapacity;
            currentAmmo = maxAmmo;
            SelectWeapon(currentWeaponIndex);
        }

        private void Update()
        {
            if (isReloading) return;

            // Check reload request
            if (inputManager != null && inputManager.reloadInput)
            {
                inputManager.reloadInput = false;
                if (currentMagazine < magazineCapacity && currentAmmo > 0)
                {
                    StartCoroutine(ReloadCoroutine());
                    return;
                }
            }

            // Automatic reload when empty
            if (currentMagazine <= 0)
            {
                if (currentAmmo > 0)
                {
                    StartCoroutine(ReloadCoroutine());
                }
                return;
            }

            // Shoot check
            if (inputManager != null && inputManager.shootInput && Time.time >= nextTimeToFire)
            {
                nextTimeToFire = Time.time + (1f / fireRate);
                Shoot();
            }
        }

        public void TriggerReload()
        {
            if (!isReloading && currentMagazine < magazineCapacity && currentAmmo > 0)
            {
                StartCoroutine(ReloadCoroutine());
            }
        }

        private void Shoot()
        {
            currentMagazine--;

            // Muzzle flash particle
            if (muzzleFlash != null)
            {
                muzzleFlash.Play();
            }

            // Play shoot animation
            if (animatorManager != null && animatorManager.animator != null)
            {
                animatorManager.animator.SetTrigger("Shoot");
            }

            // Raycast from camera center
            Ray ray = mainCamera.ViewportPointToRay(new Vector3(0.5f, 0.5f, 0f));
            RaycastHit hit;

            if (Physics.Raycast(ray, out hit, fireRange))
            {
                // Check if hit Pedestrian AI
                var pedestrian = hit.transform.GetComponent<CharacterNavigatorScript>();
                if (pedestrian != null)
                {
                    pedestrian.TakeDamage(giveDamageOf);
                    SpawnImpactEffect(fleshImpactPrefab, hit);
                    return;
                }

                // Check if hit Police Officer
                var police = hit.transform.GetComponent<PoliceOfficer>();
                if (police != null)
                {
                    police.TakeDamage(giveDamageOf);
                    SpawnImpactEffect(fleshImpactPrefab, hit);
                    return;
                }

                // Check if hit vehicle or environment
                if (hit.transform.CompareTag("Vehicle"))
                {
                    SpawnImpactEffect(metalImpactPrefab, hit);
                }
                else
                {
                    SpawnImpactEffect(defaultImpactPrefab, hit);
                }
            }
        }

        private void SpawnImpactEffect(GameObject prefab, RaycastHit hit)
        {
            if (prefab != null)
            {
                GameObject impact = Instantiate(prefab, hit.point, Quaternion.LookRotation(hit.normal));
                Destroy(impact, 2f);
            }
        }

        private IEnumerator ReloadCoroutine()
        {
            isReloading = true;

            if (animatorManager != null)
            {
                animatorManager.PlayTargetAnim("Reload", true);
            }

            yield return new WaitForSeconds(reloadTime);

            int neededAmmo = magazineCapacity - currentMagazine;
            int ammoToDeduct = Mathf.Min(neededAmmo, currentAmmo);

            currentMagazine += ammoToDeduct;
            currentAmmo -= ammoToDeduct;

            isReloading = false;
        }

        public void SelectWeapon(int weaponIndex)
        {
            if (weaponSlots == null || weaponSlots.Length == 0) return;

            for (int i = 0; i < weaponSlots.Length; i++)
            {
                if (weaponSlots[i] != null)
                {
                    weaponSlots[i].SetActive(i == weaponIndex);
                }
            }

            currentWeaponIndex = weaponIndex;
        }

        public void AddAmmo(int amount)
        {
            currentAmmo += amount;
            currentAmmo = Mathf.Min(currentAmmo, maxAmmo * 2);
        }
    }
}
