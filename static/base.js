const navbarToggle = document.querySelector('.navbar-toggle');
const navbarNav = document.querySelector('.navbar-nav');
const sidebarMainPodButton = document.querySelector('#sidebar_main_pod');
const collapsedMainPodSection = document.querySelector('#collapsed_main_pod_section');
const sidebarSubPodButton = document.querySelector('#sidebar_sub_pod');
const collapsedSubPodSection = document.querySelector('#collapsed_sub_pod_section');

navbarToggle.addEventListener('click', () => {
  navbarNav.classList.toggle('active');
});

sidebarMainPodButton.addEventListener('click', () => {
  if (collapsedMainPodSection.style.display === 'block') {
    collapsedMainPodSection.style.display = 'none'
  } else {
    collapsedMainPodSection.style.display = 'block'
  }
})

sidebarSubPodButton.addEventListener('click', (e) => {
  if (collapsedSubPodSection.style.display === 'block') {
    collapsedSubPodSection.style.display = 'none'
  } else {
    collapsedSubPodSection.style.display = 'block'
  }
})