async function loadResources(groupId){return apiCall(`/resources/groups/${groupId}`);}
async function uploadResource(groupId,formData){return apiCall(`/resources/groups/${groupId}`,{method:"POST",body:formData});}
