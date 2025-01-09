document.addEventListener("DOMContentLoaded", function () {
    // Debugging data passed from Flask
    console.log(totalSalesData, salesByItemData, quantitySoldOverTimeData, topSellingItemsData, salesDistributionData, dailySalesPerformanceData);

    // Chart 1: Total Sales
    const totalSalesdataCtx = document.getElementById("totalSales").getContext("2d");
    new Chart(totalSalesdataCtx, {
        type: "bar",
        data: {
            labels: totalSalesData.labels,
            datasets: [{
                label: "Total Sales by Admin",
                data: totalSalesData.values,
                backgroundColor: [
                    "rgba(75, 192, 192, 0.6)",
                    "rgba(54, 162, 235, 0.6)",
                    "rgba(255, 99, 132, 0.6)"
                ],
                borderColor: [
                    "rgba(75, 192, 192, 1)",
                    "rgba(54, 162, 235, 1)",
                    "rgba(255, 99, 132, 1)"
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Chart 2: Sales by Item
    const salesByItemCtx = document.getElementById("salesByItemChart").getContext("2d");
    new Chart(salesByItemCtx, {
        type: "bar",
        data: {
            labels: salesByItemData.labels,
            datasets: [{
                label: "Sales by Item",
                data: salesByItemData.values,
                backgroundColor: "rgba(75, 192, 192, 0.6)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 1
            }]
        }
    });

    // Chart 3: Quantity Sold Over Time
    const quantityOverTimeCtx = document.getElementById("quantityOverTimeChart").getContext("2d");
    new Chart(quantityOverTimeCtx, {
        type: "line",
        data: {
            labels: quantitySoldOverTimeData.labels,
            datasets: [{
                label: "Quantity Sold Over Time",
                data: quantitySoldOverTimeData.values,
                backgroundColor: "rgba(153, 102, 255, 0.6)",
                borderColor: "rgba(153, 102, 255, 1)",
                borderWidth: 2,
                fill: true
            }]
        }
    });

    // Chart 4: Top-Selling Items
    const topSellingItemsCtx = document.getElementById("topSellingItemsChart").getContext("2d");
    new Chart(topSellingItemsCtx, {
        type: "bar",
        data: {
            labels: topSellingItemsData.labels,
            datasets: [{
                label: "Top Selling Items",
                data: topSellingItemsData.values,
                backgroundColor: "rgba(255, 159, 64, 0.6)",
                borderColor: "rgba(255, 159, 64, 1)",
                borderWidth: 1
            }]
        }
    });

    // Chart 5: Sales Distribution
    const salesDistributionCtx = document.getElementById("salesDistributionChart").getContext("2d");
    new Chart(salesDistributionCtx, {
        type: "pie",
        data: {
            labels: salesDistributionData.labels,
            datasets: [{
                label: "Sales Distribution",
                data: salesDistributionData.values,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.6)',   // Pink
                    'rgba(54, 162, 235, 0.6)',   // Blue
                    'rgba(255, 206, 86, 0.6)',   // Yellow
                    'rgba(75, 192, 192, 0.6)',   // Green
                    'rgba(153, 102, 255, 0.6)',  // Purple
                    'rgba(255, 159, 64, 0.6)'
                ]
            }]
        }
    });

    // Chart 6: Daily Sales Performance
    const dailyPerformanceCtx = document.getElementById("dailyPerformanceChart").getContext("2d");
    new Chart(dailyPerformanceCtx, {
        type: "line",
        data: {
            labels: dailySalesPerformanceData.labels,
            datasets: [{
                label: "Daily Revenue",
                data: dailySalesPerformanceData.values,
                backgroundColor: "rgba(255, 205, 86, 0.6)",
                borderColor: "rgba(255, 205, 86, 1)",
                borderWidth: 2,
                fill: true
            }]
        }
    });
});
