function initializeCharts(sentimentCounts, emotionCounts) {
    // Sentiment Bar Chart
    const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
    new Chart(sentimentCtx, {
        type: 'bar',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                label: 'Sentiment Count',
                data: [sentimentCounts.POSITIVE, sentimentCounts.NEGATIVE, sentimentCounts.NEUTRAL],
                backgroundColor: ['#28a745', '#dc3545', '#6c757d'],
                borderColor: ['#1e7e34', '#c82333', '#5a6268'],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Number of Tickets' }
                }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Sentiment Distribution' }
            }
        }
    });

    // Emotion Pie Chart
    const emotionCtx = document.getElementById('emotionChart').getContext('2d');
    const emotions = Object.keys(emotionCounts);
    const counts = Object.values(emotionCounts);
    new Chart(emotionCtx, {
        type: 'pie',
        data: {
            labels: emotions.map(e => e.charAt(0).toUpperCase() + e.slice(1)),
            datasets: [{
                data: counts,
                backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40'],
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: { position: 'right' },
                title: { display: true, text: 'Emotion Distribution' }
            }
        }
    });
}