using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using GTAViceCityClone.Data;

namespace GTAViceCityClone.UI
{
    /// <summary>
    /// MainMenuManager controls Main Menu screen transitions, loading scenes, audio volume, and loading saved games.
    /// Reconstructed cleanly from Episodes 53, 54, 55, 66.
    /// </summary>
    public class MainMenuManager : MonoBehaviour
    {
        [Header("UI Panels")]
        public GameObject mainPanel;
        public GameObject optionsPanel;

        [Header("UI Controls")]
        public Slider volumeSlider;
        public Button loadGameButton;

        [Header("Game Scene Name")]
        public string gameSceneName = "GameScene";

        private void Start()
        {
            if (optionsPanel != null)
            {
                optionsPanel.SetActive(false);
            }

            if (loadGameButton != null)
            {
                loadGameButton.interactable = SaveSystem.HasSaveFile();
            }

            if (volumeSlider != null)
            {
                volumeSlider.value = AudioListener.volume;
                volumeSlider.onValueChanged.AddListener(SetVolume);
            }
        }

        public void PlayGame()
        {
            SceneManager.LoadScene(gameSceneName);
        }

        public void LoadSavedGame()
        {
            // Loads game scene where GameManager will call LoadGame() on start
            PlayerPrefs.SetInt("LoadSavedGameOnStart", 1);
            PlayerPrefs.Save();
            SceneManager.LoadScene(gameSceneName);
        }

        public void OpenOptions()
        {
            if (mainPanel != null) mainPanel.SetActive(false);
            if (optionsPanel != null) optionsPanel.SetActive(true);
        }

        public void CloseOptions()
        {
            if (optionsPanel != null) optionsPanel.SetActive(false);
            if (mainPanel != null) mainPanel.SetActive(true);
        }

        public void SetVolume(float volume)
        {
            AudioListener.volume = volume;
        }

        public void QuitGame()
        {
            Application.Quit();
        }
    }
}
