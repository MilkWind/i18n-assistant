// Sample JavaScript application with i18n calls

function initializeApp() {
    console.log(t('common.hello'));
    displayWelcomeMessage();
}

function displayWelcomeMessage() {
    const welcomeText = $t('common.welcome');
    const element = document.getElementById('welcome');
    element.textContent = welcomeText;
}

function showLoginForm() {
    const loginTitle = i18n.t('auth.login.title');
    const usernameLabel = t('auth.login.username');
    const passwordLabel = t('auth.login.password');
    const submitButton = $t('auth.login.submit');
    
    // Create form elements
    const form = createForm({
        title: loginTitle,
        fields: [
            { label: usernameLabel, type: 'text' },
            { label: passwordLabel, type: 'password' }
        ],
        submit: submitButton
    });
    
    return form;
}

function handleValidationError(field) {
    if (field === 'email') {
        return t('errors.validation.email');
    }
    return $t('errors.validation.required');
}

function navigateToPage(page) {
    switch(page) {
        case 'home':
            setPageTitle(t('navigation.home'));
            break;
        case 'about':
            setPageTitle(i18n.t('navigation.about'));
            break;
        case 'contact':
            setPageTitle($t('navigation.contact'));
            break;
        default:
            showError(t('errors.404'));
    }
}

// Some calls that won't be detected (for testing)
const notAnI18nCall = translate('some.key');
const alsoNotDetected = getText('another.key');

export { initializeApp, showLoginForm, navigateToPage }; 