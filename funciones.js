         const API_BASE_URL = 'http://127.0.0.1:5000/api'; // Asegúrate de que coincida con el puerto de tu Flask

        let commoditiesData = []; // Esta variable ahora se llenará desde el backend
        let currentCommodity = null; // Para almacenar la clave de la commodity actualmente mostrada en detalles
    
        let productionMapInstance;
        let priceChartInstanceHighcharts; 
        let comparisonChartInstanceHighcharts;

        // --- Page Navigation Logic ---
        function showPage(pageId, commodityKey = null) {
            document.querySelectorAll('.page-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(pageId).classList.add('active');

            // Special handling for details page
            if (pageId === 'details' && commodityKey) {
                currentCommodity = commodityKey;
                updateCommodityDetails(commodityKey);
            } else if (pageId === 'details' && currentCommodity) {
                // Si ya estamos en detalles y no se especifica una nueva commodity, recargar la actual
                updateCommodityDetails(currentCommodity);
            }
            // Special handling for map page to re-initialize Leaflet
            if (pageId === 'map') {
                initializeMap();
            } else if (productionMapInstance) {
                // Invalidate size when map is hidden to prevent rendering issues
                productionMapInstance.invalidateSize(true);
            }
            // Special handling for news page
            if (pageId === 'news') {
                fetchGeneralNews();
            }
            // Special handling for comparator page
            if (pageId === 'comparator') {
                populateComparisonSelects();
            }
        }
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function(event) {
                event.preventDefault();
                const pageId = this.getAttribute('data-page');
                showPage(pageId);
            });
        });

        // --- Home Page Functions ---

        // Función para obtener datos de commodities del backend
        async function fetchCommoditiesData() {
            try {
                const response = await fetch(`${API_BASE_URL}/commodities`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                commoditiesData = await response.json();
                console.log("Datos de commodities obtenidos del backend:", commoditiesData);
                renderCommoditiesTable();
                populateComparisonSelects(); // Populate selects once data is loaded
            } catch (error) {
                console.error("Error al obtener datos de commodities:", error);
                document.getElementById('commoditiesTableBody').innerHTML = `<tr><td colspan="6" class="px-6 py-4 whitespace-nowrap text-center text-red-500">Error al cargar datos. Intenta de nuevo más tarde.</td></tr>`;
            }
        }

        // Función para renderizar la tabla de commodities
        function renderCommoditiesTable() {
            const tableBody = document.getElementById('commoditiesTableBody');
            tableBody.innerHTML = ''; // Limpiar tabla

            if (commoditiesData.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 whitespace-nowrap text-center text-gray-500">No hay datos de materias primas disponibles.</td></tr>`;
                return;
            }

            commoditiesData.forEach(commodity => {
                const changeClass = commodity.change > 0 ? 'text-green-400' : (commodity.change < 0 ? 'text-red-500' : 'text-gray-300');
                const row = `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <div class="flex-shrink-0 h-10 w-10">
                                    <img src="${commodity.icon_url}" alt="Icono de ${commodity.name}" class="rounded-full">
                                </div>
                                <div class="ml-4">
                                    <div class="text-sm font-medium text-gray-300">${commodity.name}</div>
                                    <div class="text-sm text-gray-500">${commodity.symbol}</div>
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-300">$${commodity.current_price.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm ${changeClass}">${commodity.change > 0 ? '+' : ''}${commodity.change.toFixed(2)}%</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${commodity.high.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${commodity.low.toFixed(2)}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <button class="view-details-btn text-purple-500 hover:text-purple-400 text-sm font-medium" data-commodity="${commodity.key}">Ver detalles</button>
                        </td>
                    </tr>
                `;
                tableBody.insertAdjacentHTML('beforeend', row);
            });

            // Re-attach event listeners for "Ver detalles" buttons
            document.querySelectorAll('.view-details-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const commodity = this.getAttribute('data-commodity');
                    showPage('details', commodity);
                });
            });
        }

        // Fetch featured news for the home page
        async function fetchFeaturedNews() {
            const featuredNewsContainer = document.getElementById('featuredNewsContainer');
            featuredNewsContainer.innerHTML = '<p class="col-span-full text-center text-gray-500">Cargando noticias destacadas...</p>';
            try {
                const response = await fetch(`${API_BASE_URL}/news`); // Assuming this endpoint returns general news
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const news = await response.json();
                renderFeaturedNews(news.slice(0, 3)); // Show top 3 news items
            } catch (error) {
                console.error("Error al obtener noticias destacadas:", error);
                featuredNewsContainer.innerHTML = `<p class="col-span-full text-center text-red-500">Error al cargar noticias destacadas.</p>`;
            }
        }

        function renderFeaturedNews(newsItems) {
            const featuredNewsContainer = document.getElementById('featuredNewsContainer');
            featuredNewsContainer.innerHTML = '';
            if (newsItems.length === 0) {
                featuredNewsContainer.innerHTML = '<p class="col-span-full text-center text-gray-500">No hay noticias destacadas disponibles.</p>';
                return;
            }
            newsItems.forEach(newsItem => {
                const newsCard = `
                    <div class="news-card bg-gray-800 rounded-lg shadow overflow-hidden">
                        <img src="https://placehold.co/600x400/1e3c72/white?text=Noticia" alt="Imagen de noticia" class="w-full h-48 object-cover">
                        <div class="p-6">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-sm text-gray-500">${newsItem.source}</span>
                                <span class="text-sm text-gray-500">${newsItem.time}</span>
                            </div>
                            <h3 class="font-bold text-xl mb-2">${newsItem.title}</h3>
                            <p class="text-gray-400">${newsItem.snippet}</p>
                            <a href="${newsItem.url}" target="_blank" class="mt-4 text-purple-500 hover:text-purple-400 font-medium block">Leer más</a>
                        </div>
                    </div>
                `;
                featuredNewsContainer.insertAdjacentHTML('beforeend', newsCard);
            });
        }


        // --- Details Page Functions ---
        async function updateCommodityDetails(commodityKey) {
            const commodityNameDisplay = document.getElementById('commodityNameDisplay');
            const commodityIcon = document.getElementById('commodityIcon');
            const commodityTitle = document.getElementById('commodityTitle');
            const currentPriceElement = document.getElementById('currentPrice');
            const priceChangeElement = document.getElementById('priceChange');
            const detailsNewsContainer = document.getElementById('detailsNewsContainer');

            commodityNameDisplay.textContent = 'Cargando...';
            commodityIcon.src = '';
            commodityTitle.textContent = 'Cargando...';
            currentPriceElement.textContent = '';
            priceChangeElement.textContent = '';
            detailsNewsContainer.innerHTML = '<p class="text-center text-gray-500">Cargando noticias relacionadas...</p>';
            document.getElementById('priceChartContainer').innerHTML = ''; // Clear previous chart

            try {
                const response = await fetch(`${API_BASE_URL}/commodity/${commodityKey}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                console.log("Detalles de commodity obtenidos del backend:", data);

                commodityNameDisplay.textContent = data.name;
                commodityIcon.src = data.icon_url;
                commodityTitle.textContent = `${data.name} (${data.symbol})`;
                currentPriceElement.textContent = `$${data.current_price.toFixed(2)}`;
                
                const changeClass = data.change > 0 ? 'text-green-400' : (data.change < 0 ? 'text-red-500' : 'text-gray-300');
                priceChangeElement.textContent = `${data.change > 0 ? '+' : ''}${data.change}% ($${data.change_amount.toFixed(2)})`;
                priceChangeElement.className = changeClass;

                // Update related news
                detailsNewsContainer.innerHTML = ''; // Clear existing news
                if (data.news && data.news.length > 0) {
                    data.news.forEach(newsItem => {
                        const newsCard = `
                            <div class="news-card p-4 border border-gray-700 rounded-lg">
                                <h4 class="font-bold mb-2">${newsItem.title}</h4>
                                <p class="text-gray-400 mb-2">${newsItem.source} - ${newsItem.time}</p>
                                <p class="text-gray-300">${newsItem.snippet}</p>
                                <a href="${newsItem.url}" target="_blank" class="mt-2 text-purple-500 hover:text-purple-400 font-medium block">Leer más</a>
                            </div>
                        `;
                        detailsNewsContainer.insertAdjacentHTML('beforeend', newsCard);
                    });
                } else {
                    detailsNewsContainer.innerHTML = '<p class="text-center text-gray-500">No hay noticias relacionadas disponibles.</p>';
                }

                // Update price chart with 1M data by default
                updatePriceChart(data.history['1M'], 'Precio del ' + data.name + ' (USD)');

            } catch (error) {
                console.error("Error al obtener detalles de la commodity:", error);
                commodityNameDisplay.textContent = 'Error';
                commodityTitle.textContent = 'Error al cargar detalles';
                currentPriceElement.textContent = 'N/A';
                priceChangeElement.textContent = 'N/A';
                detailsNewsContainer.innerHTML = '<p class="text-center text-red-500">Error al cargar detalles o noticias.</p>';
            }
        }

        function updatePriceChart(data, label) {
            const chartOptions = {
                chart: {
                    type: 'line',
                    renderTo: 'priceChartContainer', // ID del div donde se renderizará el gráfico
                    backgroundColor: '#1A1A1A', // Fondo del gráfico (bg-gray-800)
                    style: {
                        fontFamily: 'sans-serif',
                        color: '#E0E0E0'
                    }
                },
                title: {
                    text: label,
                    style: {
                        color: '#E0E0E0' // Color del título
                    }
                },
                xAxis: {
                    // Highcharts puede inferir el eje X si los datos son solo valores Y secuenciales
                    labels: {
                        style: {
                            color: '#C0C0C0' // Color de las etiquetas del eje X
                        }
                    },
                    gridLineColor: 'rgba(255, 255, 255, 0.1)' // Color de las líneas de la cuadrícula
                },
                yAxis: {
                    title: {
                        text: 'Precio (USD)',
                        style: {
                            color: '#E0E0E0' // Color del título del eje Y
                        }
                    },
                    labels: {
                        formatter: function() {
                            return '$' + this.value.toFixed(2);
                        },
                        style: {
                            color: '#C0C0C0' // Color de las etiquetas del eje Y
                        }
                    },
                    gridLineColor: 'rgba(255, 255, 255, 0.1)' // Color de las líneas de la cuadrícula
                },
                legend: {
                    itemStyle: {
                        color: '#E0E0E0' // Color de los elementos de la leyenda
                    }
                },
                tooltip: {
                    valuePrefix: '$',
                    valueDecimals: 2,
                    backgroundColor: 'rgba(0, 0, 0, 0.7)', // Fondo del tooltip
                    borderColor: '#A700FF', // Borde del tooltip (neon purple)
                    style: {
                        color: '#E0E0E0' // Color del texto del tooltip
                    }
                },
                series: [{
                    name: label,
                    data: data,
                    color: '#A700FF', // Neon purple
                    marker: {
                        enabled: false // Opcional: deshabilitar marcadores en los puntos de datos
                    }
                }],
                credits: {
                    enabled: false // Opcional: Quitar el "Highcharts.com"
                }
            };

            // Destruir la instancia anterior si existe
            if (priceChartInstanceHighcharts) {
                priceChartInstanceHighcharts.destroy();
            }
            // Crear nueva instancia de Highcharts
            priceChartInstanceHighcharts = Highcharts.chart(chartOptions);
        }
        
        // Handle timeframe change for details chart
        document.querySelectorAll('.timeframe-btn').forEach(button => {
            button.addEventListener('click', async function() {
                document.querySelectorAll('.timeframe-btn').forEach(btn => {
                    btn.classList.remove('bg-purple-500', 'text-white');
                    btn.classList.add('bg-gray-700', 'text-gray-300');
                });
                this.classList.remove('bg-gray-700', 'text-gray-300');
                this.classList.add('bg-purple-500', 'text-white');

                const timeframe = this.getAttribute('data-timeframe');
                // Fetch commodity details again to get the history for the selected timeframe
                try {
                    const response = await fetch(`${API_BASE_URL}/commodity/${currentCommodity}`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    const historyData = data.history[timeframe];
                    updatePriceChart(historyData, 'Precio del ' + data.name + ' (USD)');
                } catch (error) {
                    console.error("Error al obtener historial para el gráfico:", error);
                    alert("No se pudo cargar el historial para el período seleccionado.");
                }
            });
        });
    
        // Investment Simulator
        document.getElementById('investmentSimulatorForm').addEventListener('submit', async function(event) {
            event.preventDefault();
            const amount = parseFloat(document.getElementById('investmentAmount').value);
            const horizon = document.getElementById('timeHorizon').value;
            const scenario = document.getElementById('marketScenario').value;

            try {
                const response = await fetch(`${API_BASE_URL}/simulate_investment`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ amount, horizon, scenario })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                document.getElementById('simInitialInvestment').textContent = result.initial_investment.toFixed(2);
                document.getElementById('simProjectedValue').textContent = result.projected_value.toFixed(2);
                document.getElementById('simPercentageChange').textContent = `${result.percentage_change.toFixed(2)}%`;
                document.getElementById('simPeriod').textContent = result.period;

                document.getElementById('simulationResult').classList.remove('hidden');
            } catch (error) {
                console.error("Error al simular inversión:", error);
                alert(`Error en la simulación: ${error.message}`);
            }
        });

        // Action buttons (simulated)
        document.getElementById('generateQuoteBtn').addEventListener('click', function() {
            alert('Generando cotización... (Esta funcionalidad requiere backend)');
        });

        document.getElementById('sendEmailBtn').addEventListener('click', async function() {
            const recipientEmail = prompt("Introduce el correo electrónico del destinatario:");
            if (!recipientEmail) return;

            const commodityName = document.getElementById('commodityNameDisplay').textContent;
            const currentPrice = document.getElementById('currentPrice').textContent;
            const priceChange = document.getElementById('priceChange').textContent;
            const quoteDetails = `Cotización actual de ${commodityName}:\nPrecio: ${currentPrice}\nCambio: ${priceChange}`;

            try {
                const response = await fetch(`${API_BASE_URL}/send_quote_email`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email: recipientEmail, commodity_name: commodityName, quote_details: quoteDetails })
                });

                const data = await response.json();
                if (response.ok) {
                    alert(data.message);
                } else {
                    alert(`Error al enviar correo: ${data.error || 'Error desconocido'}`);
                }
            } catch (error) {
                console.error("Error de red al enviar correo:", error);
                alert("Error de conexión al intentar enviar el correo.");
            }
        });

        document.getElementById('downloadReportBtn').addEventListener('click', function() {
            alert('Descargando reporte... (Esta funcionalidad requiere backend)');
        });

        // --- Comparator Page Functions ---
        function populateComparisonSelects() {
            const select1 = document.getElementById('compareCommodity1');
            const select2 = document.getElementById('compareCommodity2');
            select1.innerHTML = '<option value="">Seleccionar...</option>';
            select2.innerHTML = '<option value="">Seleccionar...</option>';

            commoditiesData.forEach(commodity => {
                const option = `<option value="${commodity.key}">${commodity.name}</option>`;
                select1.innerHTML += option;
                select2.innerHTML += option;
            });
        }

        document.getElementById('compareBtn').addEventListener('click', async function() {
            const commodity1Key = document.getElementById('compareCommodity1').value;
            const commodity2Key = document.getElementById('compareCommodity2').value;
            const period = document.getElementById('comparisonPeriod').value;

            if (!commodity1Key || !commodity2Key) {
                alert('Por favor, selecciona dos commodities para comparar.');
                return;
            }
            if (commodity1Key === commodity2Key) {
                alert('Por favor, selecciona dos commodities diferentes.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/compare_commodities`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ commodity1: commodity1Key, commodity2: commodity2Key, period: period })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const chartData = await response.json();
                
                const chartOptions = {
                    chart: {
                        type: 'line',
                        renderTo: 'comparisonChartContainer', // ID del div para el gráfico de comparación
                        backgroundColor: '#1A1A1A', // Fondo del gráfico
                        style: {
                            fontFamily: 'sans-serif',
                            color: '#E0E0E0'
                        }
                    },
                    title: {
                        text: `Comparación de Precios Históricos (${period})`,
                        style: {
                            color: '#E0E0E0'
                        }
                    },
                    xAxis: {
                        labels: {
                            style: {
                                color: '#C0C0C0'
                            }
                        },
                        gridLineColor: 'rgba(255, 255, 255, 0.1)'
                    },
                    yAxis: {
                        title: {
                            text: 'Precio (USD)',
                            style: {
                                color: '#E0E0E0'
                            }
                        },
                        labels: {
                            formatter: function() {
                                return '$' + this.value.toFixed(2);
                            },
                            style: {
                                color: '#C0C0C0'
                            }
                        },
                        gridLineColor: 'rgba(255, 255, 255, 0.1)'
                    },
                    legend: {
                        itemStyle: {
                            color: '#E0E0E0'
                        }
                    },
                    tooltip: {
                        valuePrefix: '$',
                        valueDecimals: 2,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        borderColor: '#A700FF',
                        style: {
                            color: '#E0E0E0'
                        }
                    },
                    series: [
                        {
                            name: chartData.datasets[0].label,
                            data: chartData.datasets[0].data,
                            color: '#A700FF', // Neon purple
                            marker: {
                                enabled: false
                            }
                        },
                        {
                            name: chartData.datasets[1].label,
                            data: chartData.datasets[1].data,
                            color: '#00FFFF', // Neon cyan (o el color que prefieras para el segundo commodity)
                            marker: {
                                enabled: false
                            }
                        }
                    ],
                    credits: {
                        enabled: false
                    }
                };

                // Destruir la instancia anterior si existe
                if (comparisonChartInstanceHighcharts) {
                    comparisonChartInstanceHighcharts.destroy();
                }
                // Crear nueva instancia de Highcharts
                comparisonChartInstanceHighcharts = Highcharts.chart(chartOptions);

            } catch (error) {
                console.error("Error al comparar commodities:", error);
                alert(`Error al comparar commodities: ${error.message}. Asegúrate de que los datos históricos estén disponibles para el período seleccionado.`);
            }
        });
    

        // --- Map Page Functions ---
        async function initializeMap() {
            if (productionMapInstance) {
                productionMapInstance.remove(); // Remove existing map instance if any
            }
            productionMapInstance = L.map('productionMap').setView([4.5709, -74.2973], 5); // Centered in Colombia
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(productionMapInstance);
            
            try {
                const response = await fetch(`${API_BASE_URL}/mining_locations`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const miningLocations = await response.json();

                miningLocations.forEach(location => {
                    let color;
                    if (location.production === "high") color = "#FF0000"; // Red
                    else if (location.production === "medium") color = "#FFFF00"; // Yellow
                    else color = "#00FF00"; // Green
                    
                    L.circleMarker(location.position, {
                        radius: 8,
                        fillColor: color,
                        color: "#000",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    }).addTo(productionMapInstance)
                    .bindPopup(`<b>${location.name}</b><br>Tipo: ${location.type}<br>Producción: ${location.production === "high" ? "Alta" : location.production === "medium" ? "Media" : "Baja"}`);
                });
            } catch (error) {
                console.error("Error al cargar ubicaciones mineras para el mapa:", error);
                alert("No se pudieron cargar las ubicaciones mineras en el mapa.");
            }

            productionMapInstance.invalidateSize(); // Important for map to render correctly when its container becomes visible
        }

        document.getElementById('downloadMapDataBtn').addEventListener('click', function() {
            alert('Descargando datos del mapa... (Esta funcionalidad requiere backend)');
        });

        // --- News Page Functions ---
        async function fetchGeneralNews() {
            const generalNewsContainer = document.getElementById('generalNewsContainer');
            generalNewsContainer.innerHTML = '<p class="col-span-full text-center text-gray-500">Cargando noticias...</p>';
            try {
                const response = await fetch(`${API_BASE_URL}/news`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const news = await response.json();
                renderGeneralNews(news);
            } catch (error) {
                console.error("Error al obtener noticias generales:", error);
                generalNewsContainer.innerHTML = `<p class="col-span-full text-center text-red-500">Error al cargar noticias generales.</p>`;
            }
        }

        function renderGeneralNews(newsItems) {
            const generalNewsContainer = document.getElementById('generalNewsContainer');
            generalNewsContainer.innerHTML = '';
            if (newsItems.length === 0) {
                generalNewsContainer.innerHTML = '<p class="col-span-full text-center text-gray-500">No hay noticias disponibles.</p>';
                return;
            }
            newsItems.forEach(newsItem => {
                const newsCard = `
                    <div class="news-card bg-gray-800 rounded-lg shadow overflow-hidden">
                        <img src="https://placehold.co/600x400/1e3c72/white?text=Noticia" alt="Imagen de noticia" class="w-full h-48 object-cover">
                        <div class="p-6">
                            <div class="flex justify-between items-center mb-2">
                                <span class="text-sm text-gray-500">${newsItem.source}</span>
                                <span class="text-sm text-gray-500">${newsItem.time}</span>
                            </div>
                            <h3 class="font-bold text-xl mb-2">${newsItem.title}</h3>
                            <p class="text-gray-400">${newsItem.snippet}</p>
                            <a href="${newsItem.url}" target="_blank" class="mt-4 text-purple-500 hover:text-purple-400 font-medium block">Leer más</a>
                        </div>
                    </div>
                `;
                generalNewsContainer.insertAdjacentHTML('beforeend', newsCard);
            });
        }

        // --- Login Page Functions ---
        document.getElementById('loginForm').addEventListener('submit', async function(event) {
            event.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const loginMessage = document.getElementById('loginMessage');

            try {
                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (response.ok) {
                    loginMessage.className = 'text-center text-green-400 text-sm mt-6';
                    loginMessage.textContent = data.message;
                    alert(`Bienvenido, ${data.user.username}!`);
                    // Opcional: redirigir o actualizar UI
                    showPage('home'); // Go back to home page after login
                } else {
                    loginMessage.className = 'text-center text-red-500 text-sm mt-6';
                    loginMessage.textContent = data.error || 'Error al iniciar sesión.';
                }
            } catch (error) {
                console.error("Error de red al intentar login:", error);
                loginMessage.className = 'text-center text-red-500 text-sm mt-6';
                loginMessage.textContent = 'Error de conexión. Intenta de nuevo.';
            }
        });

        // --- Register Page Functions ---
        document.getElementById('registerForm').addEventListener('submit', async function(event) {
            event.preventDefault();
            const username = document.getElementById('registerUsername').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            const confirmPassword = document.getElementById('registerConfirmPassword').value;
            const registerMessage = document.getElementById('registerMessage');

            if (password !== confirmPassword) {
                registerMessage.className = 'text-center text-red-500 text-sm mt-6';
                registerMessage.textContent = 'Las contraseñas no coinciden.';
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                const data = await response.json();
                if (response.ok) {
                    registerMessage.className = 'text-center text-green-400 text-sm mt-6';
                    registerMessage.textContent = data.message;
                    alert("Registro exitoso. Ahora puedes iniciar sesión.");
                    showPage('login'); // Go to login page after successful registration
                } else {
                    registerMessage.className = 'text-center text-red-500 text-sm mt-6';
                    registerMessage.textContent = data.error || 'Error al registrar usuario.';
                }
            } catch (error) {
                console.error("Error de red al intentar registrar:", error);
                registerMessage.className = 'text-center text-red-500 text-sm mt-6';
                registerMessage.textContent = 'Error de conexión. Intenta de nuevo.';
            }
        });


        // --- Initial Page Load ---
        document.addEventListener('DOMContentLoaded', async function() {
            await fetchCommoditiesData(); // Fetch and render commodities for the home page
            fetchFeaturedNews(); // Fetch and render featured news for the home page
            showPage('home'); // Show the home page by default
        });