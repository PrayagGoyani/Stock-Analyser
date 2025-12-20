let stockChart = null;
let currentData = null;

document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const symbol = document.getElementById('symbol').value.toUpperCase().trim();
    const period = document.getElementById('period').value;
    const window = parseInt(document.getElementById('window').value);
    
    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const btnLoader = analyzeBtn.querySelector('.btn-loader');
    const errorDiv = document.getElementById('error');
    const resultsDiv = document.getElementById('results');
    
    // Show loading state
    analyzeBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'none';
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symbol, period, window })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'An error occurred');
        }
        
        // Store current data for downloads
        currentData = data;
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    } finally {
        // Reset button state
        analyzeBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
});

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'block';
    
    // Update header
    document.getElementById('resultsTitle').textContent = `${data.symbol} - ${data.period}`;
    
    // Update trend badge
    const trendBadge = document.getElementById('trendBadge');
    const changePercent = data.stats.change_percent;
    if (changePercent > 0) {
        trendBadge.textContent = `↑ +${changePercent.toFixed(2)}%`;
        trendBadge.className = 'trend-badge positive';
    } else if (changePercent < 0) {
        trendBadge.textContent = `↓ ${changePercent.toFixed(2)}%`;
        trendBadge.className = 'trend-badge negative';
    } else {
        trendBadge.textContent = `→ 0.00%`;
        trendBadge.className = 'trend-badge neutral';
    }
    
    // Update statistics
    document.getElementById('latestPrice').textContent = `$${data.stats.latest_price.toFixed(2)}`;
    document.getElementById('minPrice').textContent = `$${data.stats.min_price.toFixed(2)}`;
    document.getElementById('maxPrice').textContent = `$${data.stats.max_price.toFixed(2)}`;
    document.getElementById('avgPrice').textContent = `$${data.stats.avg_price.toFixed(2)}`;
    
    // Update trend text
    document.getElementById('trendText').textContent = data.trend_summary;
    
    // Display plot image
    const plotImage = document.getElementById('plotImage');
    plotImage.src = 'data:image/png;base64,' + data.plot;
    plotImage.style.display = 'block';
    
    // Create/update chart
    createChart(data);
}

function createChart(data) {
    const ctx = document.getElementById('stockChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (stockChart) {
        stockChart.destroy();
    }
    
    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Closing Price',
                    data: data.closing_prices,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 5
                },
                {
                    label: `${parseInt(document.getElementById('window').value)}-Day Moving Average`,
                    data: data.moving_avg,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 12,
                            weight: 'bold'
                        },
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Date',
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Price ($)',
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        },
                        font: {
                            size: 11
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Download CSV
document.getElementById('downloadCsvBtn').addEventListener('click', async () => {
    if (!currentData) return;
    
    try {
        const response = await fetch('/download_csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                csv_data: currentData.csv_data,
                symbol: currentData.symbol,
                period: currentData.period
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to download CSV');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentData.symbol}_${currentData.period}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert('Error downloading CSV: ' + error.message);
    }
});

// Download Plot
document.getElementById('downloadPlotBtn').addEventListener('click', () => {
    if (!currentData) return;
    
    const plotImage = document.getElementById('plotImage');
    const link = document.createElement('a');
    link.href = plotImage.src;
    link.download = `${currentData.symbol}_${currentData.period}_plot.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

