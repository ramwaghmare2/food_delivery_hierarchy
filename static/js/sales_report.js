document.addEventListener("DOMContentLoaded", function () {
    // Fetching data attributes from HTML
    const totalSalesData = JSON.parse(document.getElementById('chart-data').getAttribute('data-sales-by-date'));
    const salesByItemData = JSON.parse(document.getElementById('chart-data').getAttribute('data-sales-by-item'));

    // Debugging data passed from Flask to ensure it's correct
    console.log("Total Sales Data:", totalSalesData);
    console.log("Sales By Item Data:", salesByItemData);

    // Extracting dates and total sales from totalSalesData for the line chart
    const dates = totalSalesData.map(item => item.sale_date);
    const sales = totalSalesData.map(item => item.total_sales);

    // Bar Chart Configuration
    const barCtx = document.getElementById('sales-bar-chart').getContext('2d');
    new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: ['Total Sales', 'Quantity Sold', 'Total Orders'],
            datasets: [{
                label: 'Statistics',
                data: [
                    {{ total_sales_amount | default(0) }},
                    {{ quantity_sold | default(0) }},
                    {{ total_orders_count | default(0) }}
                ],
                backgroundColor: ['#4caf50', '#f57c00', '#2196f3'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true
        }
    });

    // Line Chart Configuration
    const lineCtx = document.getElementById('sales-line-chart').getContext('2d');
    new Chart(lineCtx, {
        type: 'line',
        data: {
            labels: dates,  // Use the extracted dates for X-axis
            datasets: [{
                label: 'Sales (₹)',
                data: sales,  // Use the extracted sales for Y-axis
                borderColor: '#03a9f4',
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Sales Amount (₹)'
                    }
                }
            }
        }
    });
});
