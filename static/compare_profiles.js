const allHobbies = document.querySelectorAll('.all_hobbies_container')
const listOfProfileHobbies = []

// get a text of current user hobbies and add it to a listOfProfileHobbie
for (let hobby of allHobbies[0].lastElementChild.children) {
    listOfProfileHobbies.push(hobby.textContent.trim())
}

// if there are two containers to compare, like when current user is looking at another
// user profile
if (allHobbies.length > 1) {
    // get each item from a list of allHobbies, should be 2
    for (let hobbiesContainer of allHobbies) {
        // then grab a list of li elements which we will itterate over
        for (let hobbyName of hobbiesContainer.lastElementChild.children) {
            // if the listOfProfileHobbies inclused text contained in li element
            if (listOfProfileHobbies.includes(hobbyName.textContent.trim())) {
                // move that li element to the top
                hobbiesContainer.lastElementChild.prepend(hobbyName)
                hobbyName.classList.remove('white_font')
                hobbyName.classList.add('yellow_font')
            }
        }
    }
}