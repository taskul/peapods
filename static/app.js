const client = new Twilio.Conversations.Client(token);
const signupForm = document.querySelector('#signup_form')
const loginForm = document.querySelector('#login_form')
const loginButtonSwitch = document.querySelector('.login_button_switch')


const navbarToggle = document.querySelector('.navbar-toggle');
const navbarNav = document.querySelector('.navbar-nav');

loginForm.style.visibility = 'hidden'

navbarToggle.addEventListener('click', () => {
  navbarNav.classList.toggle('active');
});
