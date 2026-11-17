using UnityEngine;
using UnityEngine.SceneManagement;

namespace GTAViceCityClone.UI
{
    /// <summary>
    /// PauseMenu controls game timeScale pausing, UI visibility, resuming, and scene restarting.
    /// Reconstructed cleanly from Episodes 56, 73.
    /// </summary>
    public class PauseMenu : MonoBehaviour
    {
        [Header("Pause UI Panel")]
        public GameObject pauseMenuUI;
        public static bool isGamePaused = false;

        private void Start()
        {
            if (pauseMenuUI != null)
            {
                pauseMenuUI.SetActive(false);
            }
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                if (isGamePaused)
                {
                    Resume();
                }
                else
                {
                    Pause();
                }
            }
        }

        public void Resume()
        {
            if (pauseMenuUI != null)
            {
                pauseMenuUI.SetActive(false);
            }

            Time.timeScale = 1f;
            isGamePaused = false;
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }

        public void Pause()
        {
            if (pauseMenuUI != null)
            {
                pauseMenuUI.SetActive(true);
            }

            Time.timeScale = 0f;
            isGamePaused = true;
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        public void RestartScene()
        {
            Time.timeScale = 1f;
            isGamePaused = false;
            SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
        }

        public void LoadMainMenu(string sceneName = "MainMenu")
        {
            Time.timeScale = 1f;
            isGamePaused = false;
            SceneManager.LoadScene(sceneName);
        }

        public void QuitGame()
        {
            Application.Quit();
        }
    }
}
