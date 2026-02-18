"""Widget for LLM-based caption analysis."""

from __future__ import annotations

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from loguru import logger


class CaptionAnalysisWidget(QtWidgets.QWidget):
    """Compact widget for LLM caption analysis with collapsible settings."""
    
    # Signal emitted when analysis is requested
    analysisRequested = QtCore.pyqtSignal(str, str, str)  # (provider, model, api_key)
    
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._settings = QtCore.QSettings("LabelVid", "LLMAnalysis")
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self) -> None:
        """Initialize the UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # Main button row (always visible)
        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(4)
        
        # Analyze button (compact)
        self.analyzeBtn = QtWidgets.QPushButton("🤖 Analyze & Fill Clips")
        self.analyzeBtn.setStyleSheet(
            "QPushButton {"
            "  background-color: #2196F3;"
            "  color: white;"
            "  padding: 4px 8px;"
            "  font-size: 12px;"
            "  border-radius: 3px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #1976D2;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #666;"
            "}"
        )
        self.analyzeBtn.clicked.connect(self._on_analyze_clicked)
        button_row.addWidget(self.analyzeBtn)
        
        # Settings toggle button (small)
        self.settingsBtn = QtWidgets.QPushButton("⚙️")
        self.settingsBtn.setCheckable(True)
        self.settingsBtn.setMaximumWidth(30)
        self.settingsBtn.setToolTip("Show/hide LLM settings")
        self.settingsBtn.setStyleSheet(
            "QPushButton {"
            "  padding: 4px;"
            "  font-size: 12px;"
            "  border-radius: 3px;"
            "}"
        )
        self.settingsBtn.toggled.connect(self._toggle_settings)
        button_row.addWidget(self.settingsBtn)
        
        main_layout.addLayout(button_row)
        
        # Status label (compact, always visible)
        self.statusLabel = QtWidgets.QLabel("")
        self.statusLabel.setWordWrap(True)
        self.statusLabel.setStyleSheet("font-size: 10px; color: #666;")
        main_layout.addWidget(self.statusLabel)
        
        # Collapsible settings panel
        self.settingsPanel = QtWidgets.QGroupBox("LLM Settings")
        self.settingsPanel.setVisible(False)
        settings_layout = QtWidgets.QFormLayout(self.settingsPanel)
        settings_layout.setContentsMargins(8, 8, 8, 8)
        settings_layout.setSpacing(4)
        settings_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        settings_layout.setLabelAlignment(Qt.AlignRight)
        
        # Provider selection (compact)
        self.providerCombo = QtWidgets.QComboBox()
        self.providerCombo.addItems(["OpenAI", "Gemini", "Claude"])
        self.providerCombo.currentIndexChanged.connect(self._on_provider_changed)
        self.providerCombo.setStyleSheet("font-size: 11px;")
        settings_layout.addRow("Provider:", self.providerCombo)
        
        # Model selection (compact)
        self.modelCombo = QtWidgets.QComboBox()
        self.modelCombo.setStyleSheet("font-size: 11px;")
        self._update_model_list()
        settings_layout.addRow("Model:", self.modelCombo)
        
        # API Key input with show button (compact)
        apiKeyLayout = QtWidgets.QHBoxLayout()
        apiKeyLayout.setSpacing(2)
        self.apiKeyInput = QtWidgets.QLineEdit()
        self.apiKeyInput.setEchoMode(QtWidgets.QLineEdit.Password)
        self.apiKeyInput.setPlaceholderText("API key (or use env var)")
        self.apiKeyInput.setStyleSheet("font-size: 11px;")
        apiKeyLayout.addWidget(self.apiKeyInput)
        
        self.showKeyBtn = QtWidgets.QPushButton("👁")
        self.showKeyBtn.setMaximumWidth(25)
        self.showKeyBtn.setCheckable(True)
        self.showKeyBtn.setToolTip("Show/hide API key")
        self.showKeyBtn.toggled.connect(self._toggle_api_key_visibility)
        apiKeyLayout.addWidget(self.showKeyBtn)
        
        settings_layout.addRow("API Key:", apiKeyLayout)
        
        # Save API Key checkbox (inline, compact)
        self.saveApiKeyCheckbox = QtWidgets.QCheckBox("Save key locally")
        self.saveApiKeyCheckbox.setStyleSheet("color: #888; font-size: 10px;")
        settings_layout.addRow("", self.saveApiKeyCheckbox)
        
        main_layout.addWidget(self.settingsPanel)
    
    def _toggle_settings(self, checked: bool) -> None:
        """Toggle settings panel visibility."""
        self.settingsPanel.setVisible(checked)
    
    def _on_provider_changed(self, index: int) -> None:
        """Handle provider selection change."""
        self._update_model_list()
        self._load_api_key_for_provider()
    
    def _update_model_list(self) -> None:
        """Update model list based on selected provider."""
        provider_index = self.providerCombo.currentIndex()
        
        models = {
            0: [  # OpenAI
                "gpt-5",
                "gpt-5-mini",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
            ],
            1: [  # Gemini
                "gemini-3-flash-preview",
            ],
            2: [  # Claude
                "claude-sonnet-4-6",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
            ],
        }
        
        self.modelCombo.clear()
        self.modelCombo.addItems(models.get(provider_index, []))
    
    def _update_env_hint(self) -> None:
        """Update environment variable hint."""
        provider_index = self.providerCombo.currentIndex()
        
        env_vars = {
            0: "OPENAI_API_KEY",
            1: "GEMINI_API_KEY",
            2: "ANTHROPIC_API_KEY",
        }
        
        var_name = env_vars.get(provider_index, "")
        self.envHint.setText(f"Or set environment variable: {var_name}")
    
    def _toggle_api_key_visibility(self, checked: bool) -> None:
        """Toggle API key visibility."""
        if checked:
            self.apiKeyInput.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.apiKeyInput.setEchoMode(QtWidgets.QLineEdit.Password)
    
    def _on_analyze_clicked(self) -> None:
        """Handle analyze button click."""
        provider_index = self.providerCombo.currentIndex()
        provider_names = ["openai", "gemini", "claude"]
        provider = provider_names[provider_index]
        
        model = self.modelCombo.currentText()
        api_key = self.apiKeyInput.text().strip() or None
        
        # Save settings if checkbox is checked
        if self.saveApiKeyCheckbox.isChecked():
            self._save_settings()
        else:
            # If unchecked, clear saved API key for this provider
            self._clear_api_key_for_provider()
        
        # Emit signal
        self.analysisRequested.emit(provider, model, api_key)
    
    def setEnabled(self, enabled: bool) -> None:
        """Enable/disable the widget."""
        super().setEnabled(enabled)
        self.analyzeBtn.setEnabled(enabled)
    
    def setStatus(self, message: str, is_error: bool = False) -> None:
        """Set status message.
        
        Args:
            message: Status message to display
            is_error: Whether this is an error message
        """
        color = "#f44336" if is_error else "#4CAF50"
        self.statusLabel.setStyleSheet(f"color: {color};")
        self.statusLabel.setText(message)
    
    def _save_settings(self) -> None:
        """Save current settings to QSettings."""
        provider_index = self.providerCombo.currentIndex()
        provider_names = ["openai", "gemini", "claude"]
        provider = provider_names[provider_index]
        
        # Save provider and model
        self._settings.setValue("last_provider", provider)
        self._settings.setValue("last_model", self.modelCombo.currentText())
        
        # Save API key if provided
        api_key = self.apiKeyInput.text().strip()
        if api_key:
            self._settings.setValue(f"api_key_{provider}", api_key)
            logger.info("Saved API key for provider: {}", provider)
    
    def _load_settings(self) -> None:
        """Load settings from QSettings."""
        # Load last provider
        last_provider = self._settings.value("last_provider", "openai")
        provider_names = ["openai", "gemini", "claude"]
        if last_provider in provider_names:
            self.providerCombo.setCurrentIndex(provider_names.index(last_provider))
        
        # Load last model
        last_model = self._settings.value("last_model", "")
        if last_model:
            index = self.modelCombo.findText(last_model)
            if index >= 0:
                self.modelCombo.setCurrentIndex(index)
        
        # Load API key for current provider
        self._load_api_key_for_provider()
    
    def _load_api_key_for_provider(self) -> None:
        """Load saved API key for the current provider."""
        provider_index = self.providerCombo.currentIndex()
        provider_names = ["openai", "gemini", "claude"]
        provider = provider_names[provider_index]
        
        # Load API key
        api_key = self._settings.value(f"api_key_{provider}", "")
        if api_key:
            self.apiKeyInput.setText(api_key)
            self.saveApiKeyCheckbox.setChecked(True)
            logger.debug("Loaded saved API key for provider: {}", provider)
        else:
            self.apiKeyInput.clear()
            self.saveApiKeyCheckbox.setChecked(False)
    
    def _clear_api_key_for_provider(self) -> None:
        """Clear saved API key for the current provider."""
        provider_index = self.providerCombo.currentIndex()
        provider_names = ["openai", "gemini", "claude"]
        provider = provider_names[provider_index]
        
        self._settings.remove(f"api_key_{provider}")
        logger.info("Cleared saved API key for provider: {}", provider)
