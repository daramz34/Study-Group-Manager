async function loadGroup(groupId){const [group,goals]=await Promise.all([apiCall(`/groups/${groupId}`),apiCall(`/goals/group/${groupId}`)]);return {group,goals};}
async function createGoal(groupId,payload){return apiCall(`/goals/group/${groupId}`,{method:"POST",body:JSON.stringify(payload)});}
