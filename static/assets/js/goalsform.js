let currentQuestion = 0;
const questions = document.querySelectorAll('.question');
const prevButton = document.getElementById('prevBtn');
const nextButton = document.getElementById('nextBtn');
const submitButton = document.getElementById('submitBtn');
const responseContainer = document.getElementById('responseContainer');

function showQuestion(index) {
    questions.forEach((q, i) => {
        if (i === index) {
            q.style.display = 'block';
        } else {
            q.style.display = 'none';
        }
    });

    prevButton.style.display = index === 0 ? 'none' : 'block';
    nextButton.style.display = index === questions.length - 1 ? 'none' : 'block';
    submitButton.style.display = index === questions.length - 1 ? 'block' : 'none';
}

function prevQuestion() {
    if (currentQuestion > 0) {
        currentQuestion--;
        showQuestion(currentQuestion);
    }
}

function nextQuestion() {
    if (currentQuestion < questions.length - 1) {
        currentQuestion++;
        showQuestion(currentQuestion);
    }
}

function submitForm() {
        const responses = [];

        // Define questions array
        const questions = document.querySelectorAll('input[name^="response"]');

         for (let i = 1; i <= 5; i++) {
        const response = document.getElementsByName(`response${i}`)[0].value;
        responses.push(response);
    }

        // Display the responses
        const responseContainer = document.getElementById('responseContainer');
        responseContainer.style.display = 'block';
        responseContainer.innerHTML = responses.join('<br>');

        // // Reset the form (optional)
        // document.getElementById('questions').reset();

        // Send the responses to the server using fetch
        fetch('/home/goal', {
            method: 'POST',
            body: JSON.stringify({ responses }),
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data); // Handle the response from the server
        })
        .catch(error => {
            console.error('Error:', error);
        });

        return false; // Prevent the form from traditional submission
    }
showQuestion(currentQuestion);
