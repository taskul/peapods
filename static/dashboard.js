const thingsToDO = document.querySelector('#things_to_do');

let listOfLoc;
let listOfLocDetails = [];


// Get a list of ids for near by attractions
async function searchNearBy() {
    response = await axios.get('/todo/nearby/attractions')
    listOfLoc = response['data']
}

// Get details on attractions nearby by passing their id to API
async function getLocDetails(loc_id) {
    response = await axios.get('todo/nearby/details/' + loc_id)
    listOfLocDetails.push(response['data'])
    localStorage.setItem('attractionDetails', JSON.stringify(listOfLocDetails))
}

// Create attractios nearby elements
function createAttractionElements(loc_name, rating_img, linkToTA, linkToWebsite) {
    box = document.createElement('div')
    box.classList.add('attractions_container')
    title = document.createElement('p')
    title.classList.add('pod_thumbnail_text_title')
    title.textContent = loc_name
    rating = document.createElement('img')
    rating.setAttribute('src', rating_img)
    linkToTrip = document.createElement('a')
    linkToTrip.classList.add('pod_thumbnail_text')
    linkToTrip.setAttribute('href', linkToTA)
    linkToTrip.textContent = 'Detials'
    website = document.createElement('a')
    website.classList.add('pod_thumbnail_text')
    website.setAttribute('href', linkToWebsite)
    website.textContent = 'Website'
    box.append(title)
    box.append(rating)
    box.append(linkToTrip)
    box.append(website)
    thingsToDO.append(box)
}

function loopThroughLocDetails() {
    for (let locWithDetails of listOfLocDetails) {
        createAttractionElements(
            loc_name = locWithDetails['name'],
            rating_img = locWithDetails['rating_image_url'],
            linkToTA = locWithDetails['web_url'],
            linkToWebsite = locWithDetails['website']
        )
    }

}

async function createListOfAttractions() {
    if (localStorage.getItem('attractionsDetails')) {
        listOfLocDetails = JSON.parse(localStorage.getItem('attractionsDetails'))
        loopThroughLocDetails()
        document.querySelector('.loader').remove()
    } else {
        await searchNearBy()
        for (let loc of listOfLoc) {
            await getLocDetails(loc)
        }
        for (let locDetails of listOfLocDetails) {
        }
        loopThroughLocDetails()
        document.querySelector('.loader').remove()
    }
}

createListOfAttractions()

// ----------------------------------highlighing matching hobbies--------------
const teamMembers = document.querySelectorAll('.team_member_thumbnail')
const userHobbiesUl = document.getElementById('current_user_hobbies')
const currentUserHobbies = document.querySelectorAll('#current_user_hobbies li')
const listOfUserHobbies = []

// get a text of current user hobbies and add it to a listOfUserHobbies
for (let hobby of currentUserHobbies) {
    listOfUserHobbies.push(hobby.textContent.trim())
}

// making sure only 5 li items show up in a profile thumbnail
while (userHobbiesUl.children.length > 5) {
    userHobbiesUl.removeChild(userHobbiesUl.lastElementChild)
}

// loop through team member div elements
teamMembers.forEach((member) => {
    // get the ul and li elements
    let ulElement = member.querySelector('ul')
    let liElements = member.querySelectorAll('li')
    // loop over li elements
    liElements.forEach((liItem) => {
        if (listOfUserHobbies.includes(liItem.textContent.trim())) {
            ulElement.prepend(liItem)
            liItem.classList.remove('white_font')
            liItem.classList.add('yellow_font')
        }
        
    })
    // making sure only 5 li items show up in a profile thumbnail
    while (ulElement.children.length > 5) {
        ulElement.removeChild(ulElement.lastElementChild)
    }
});

// sort all team member div elements, check if there are any li elements that have a 
// yellow_font class, and if they do assign them to a variable name liItemElements
// then within a div element we now have that variable liItemElements to which we 
// can assign the number of li elements that have yellow_font class, we will use
// this for sorting.
teamMembers.forEach((member) => {
    const ulElement = member.querySelector('ul')
    let liItemElements = ulElement.querySelectorAll('li.yellow_font');
    member.liItemElements = liItemElements.length;

})

// create an array of div elements that is sorted based on a numeric value inside
// liItemElements of each member div
const sortedDivElements = Array.from(teamMembers).sort((a, b) => {
    const liCountA = a.liItemElements;
    const liCountB = b.liItemElements;
    if (liCountA < liCountB) {
        return 1;
    } else if (liCountA > liCountB) {
        return -1;
    }
    return 0;
});

// Add sorted memeber div elemnts to a container for all team members. 
const teamMembersDiv = document.querySelector('.team_members')
sortedDivElements.forEach((div) => {
    teamMembersDiv.appendChild(div);
});
    