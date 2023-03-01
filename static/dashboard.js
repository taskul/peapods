const loginButton = document.querySelector('.button-primary');
const thingsToDO = document.querySelector('#things_to_do');

const navbarToggle = document.querySelector('.navbar-toggle');
const navbarNav = document.querySelector('.navbar-nav');
let listOfLoc;
let listOfLocDetails = [];

navbarToggle.addEventListener('click', () => {
    navbarNav.classList.toggle('active');
});

// Get a list of ids for near by attractions
async function searchNearBy() {
    response = await axios.get('/todo/nearby/attractions')
    listOfLoc = response['data']
}

// Get details on attractions nearby by passing their id to API
async function getLocDetails(loc_id) {
    response = await axios.get('todo/nearby/details/' + loc_id)
    listOfLocDetails.push(response['data'])
    localStorage.setItem('attractionDetails', listOfLocDetails)
}

// Create attractios nearby elements
function createAttractionElements(loc_name, rating_img, linkToTA, linkToWebsite) {
    box = document.createElement('div')
    box.classList.add('attraction')
    title = document.createElement('p')
    title.classList.add('attraction_title')
    title.textContent = loc_name
    rating = document.createElement('img')
    rating.setAttribute('src', rating_img)
    linkToTrip = document.createElement('a')
    linkToTrip.classList.add('attraction_link')
    linkToTrip.setAttribute('href', linkToTA)
    linkToTrip.textContent = 'Detials'
    website = document.createElement('a')
    website.classList.add('attraction_link')
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
        listOfLocDetails = localStorage.getItem('attractionsDetails')
        loopThroughLocDetails()
        document.querySelector('.loader').remove()
    } else {
        await searchNearBy()
        for (let loc of listOfLoc) {
            await getLocDetails(loc)
        }
        for (let locDetails of listOfLocDetails) {
            console.log(locDetails)
        }
        loopThroughLocDetails()
        document.querySelector('.loader').remove()
    }
}

createListOfAttractions()
