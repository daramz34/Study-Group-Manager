async function loadLeaderboard(groupId,week){return apiCall(`/leaderboard/${groupId}${week?`?week=${week}`:""}`);}
