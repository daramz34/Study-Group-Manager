async function startQuiz(goalId){return apiCall(`/quiz/goals/${goalId}/start-quiz`,{method:"POST"});}
async function submitQuiz(quizId,answers){return apiCall(`/quiz/${quizId}/submit`,{method:"POST",body:JSON.stringify({answers})});}
