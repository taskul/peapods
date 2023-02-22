// const client = new Twilio.Conversations.Client(token);
const signupForm = document.querySelector('#signup_form')
const loginForm = document.querySelector('#login_form')
const loginButtonSwitch = document.querySelector('.login_button_switch')
const smallFormContainer = document.querySelector('.small_forms_container')
const loginButton = document.querySelector('.button-primary')

loginButton.style.visibility = 'hidden'


const navbarToggle = document.querySelector('.navbar-toggle');
const navbarNav = document.querySelector('.navbar-nav');

loginForm.style.display = 'none';
smallFormContainer.style.display = "none";

navbarToggle.addEventListener('click', () => {
  navbarNav.classList.toggle('active');
});
