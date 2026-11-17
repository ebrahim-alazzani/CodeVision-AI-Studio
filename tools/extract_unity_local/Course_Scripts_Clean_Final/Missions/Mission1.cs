using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using GTAViceCityClone.UI;

namespace GTAViceCityClone.Missions
{
    /// <summary>
    /// Mission1 manages the first storyline mission: trigger checkpoint, cutscene playback, target assassination, and money reward.
    /// Reconstructed cleanly from Episodes 58, 59, 60, 61, 62, 63.
    /// </summary>
    public class Mission1 : MonoBehaviour
    {
        [Header("Mission Markers & Locations")]
        public Transform missionTriggerMarker;
        public Transform mansionTargetMarker;
        public GameObject cutsceneCamera;
        public GameObject missionUI;
        public Text missionObjectiveText;
        public GameObject missionPassedBanner;

        [Header("Mission State")]
        public bool isMissionActive = false;
        public bool isCutscenePlaying = false;
        public bool isTargetEliminated = false;
        public bool isMissionCompleted = false;

        [Header("Mission Targets")]
        public Character targetBoss;
        public Guard[] mansionGuards;

        [Header("Reward")]
        public int rewardMoney = 5000;

        private void Start()
        {
            if (cutsceneCamera != null) cutsceneCamera.SetActive(false);
            if (missionUI != null) missionUI.SetActive(false);
            if (missionPassedBanner != null) missionPassedBanner.SetActive(false);
        }

        private void Update()
        {
            if (isMissionActive && !isTargetEliminated)
            {
                if (targetBoss != null && targetBoss.isDead)
                {
                    isTargetEliminated = true;
                    CompleteMission();
                }
            }
        }

        public void TriggerMissionStart()
        {
            if (isMissionActive || isMissionCompleted) return;

            StartCoroutine(PlayIntroCutscene());
        }

        private IEnumerator PlayIntroCutscene()
        {
            isCutscenePlaying = true;
            if (cutsceneCamera != null) cutsceneCamera.SetActive(true);

            // Dialogue / cinematic delay
            yield return new WaitForSeconds(4f);

            if (cutsceneCamera != null) cutsceneCamera.SetActive(false);
            isCutscenePlaying = false;

            StartMissionGameplay();
        }

        private void StartMissionGameplay()
        {
            isMissionActive = true;
            if (missionUI != null)
            {
                missionUI.SetActive(true);
                if (missionObjectiveText != null)
                {
                    missionObjectiveText.text = "Infiltrate the Mansion and Eliminate the Boss!";
                }
            }

            if (mansionTargetMarker != null)
            {
                mansionTargetMarker.gameObject.SetActive(true);
            }
        }

        public void CompleteMission()
        {
            if (isMissionCompleted) return;

            isMissionCompleted = true;
            isMissionActive = false;

            StartCoroutine(MissionPassedSequence());
        }

        private IEnumerator MissionPassedSequence()
        {
            if (missionUI != null) missionUI.SetActive(false);
            if (missionPassedBanner != null) missionPassedBanner.SetActive(true);

            if (GameManager.Instance != null)
            {
                GameManager.Instance.AddMoney(rewardMoney);
                GameManager.Instance.currentMissionIndex = 1;
            }

            yield return new WaitForSeconds(5f);

            if (missionPassedBanner != null)
            {
                missionPassedBanner.SetActive(false);
            }
        }
    }
}
