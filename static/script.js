Chart.register(ChartStreaming);
Chart.defaults.set('plugins.streaming', {
    duration: 20000
  });

var base_url = window.location.href;
var liveChart = null;
var wordChart = null;

$(function() {
    liveChart = new Chart(
        document.getElementById('chats-per-sec'),
        {
            type: 'line',
            data: {
                datasets: [
                    {
                        tension: 0.3,
                        fill: true,
                        label: '초당 채팅 수',
                        data: []
                    }
                ]
            },
            options: {
                scales: {
                    x: {
                        type: 'realtime',
                        realtime: {
                            delay: 4000
                        }
                    },
                    y: {
                        min: 0,
                        max: 300
                    }
                }
            }
        }
        );
    wordChart = new Chart(
        document.getElementById('words-per-day'),
        {
            type: 'line',
            data: {
                datasets: [
                    {
                        tension: 0.3,
                        fill: true,
                        data: []
                    }
                ]
            }
        }
    );

    setInterval(function() {
        $.ajax({
            url: base_url + 'chats_per_sec',
            type: 'GET',
            success: (data, textStatus, jqXHR) => {
                var series =  liveChart.data.datasets[0].data;
                var latest_data_time = 0;
                if (series.length > 0) {
                    latest_data_time = series[series.length - 1]['x'];
                }

                $.each(data, function(idx, value) {
                    var time = Date.parse(value[1]);
                    if (latest_data_time < time) {
                        series.push({
                            x : time,
                            y : value[0]
                        });
                        $('.chats-per-sec-span').text(value[0] +'chats/sec')
                    }
                });
                liveChart.update();
            },
            error : function(XMLHttpRequest, textStatus, errorThrown) { 
                alert("error : " + errorThrown)
            }
        });
    }, 1000);

    load_list();
});

function load_list() {
    $("#word-list").html('');
    $.ajax({
        url: base_url + 'statistics/word',
        type: 'GET',
        success: (data, textStatus, jqXHR) => {  
            $.each(data, function(key, value) {
                $('#word-list').append('<li class="word-list-item" name="' + key + '">'
                + '<div class="word-list-item-key-container">'
                    + '<span class="word-list-item-key">' + key + '</span>'
                + '</div>'
                + '<div class="word-list-item-value-container">'
                    + '<span class="word-list-item-value">' + value + '</span>'
                + '</div></li>');
            });

            $('.word-list-item').click(function(){
                load_chart($(this).attr('name'));
            });
        },
        error : function(XMLHttpRequest, textStatus, errorThrown) { 
            alert("error : " + errorThrown)
        }
    });
}

function load_chart(word) {
    $.ajax({
        url: base_url + 'statistics/word/' + word,
        type: 'GET',
        success: (data, textStatus, jqXHR) => {  
            wordChart.data.datasets[0].data = data;
            wordChart.data.datasets[0].label = word;
            wordChart.update();
        },
        error : function(XMLHttpRequest, textStatus, errorThrown) { 
            alert("error : " + errorThrown)
        }
    });
}

