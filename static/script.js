Chart.register(ChartStreaming);
Chart.defaults.set('plugins.streaming', {
    duration: 20000
});

var base_url = window.location.href;
var liveChart = null;
var wordChart = null;

$(function () {
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
                maintainAspectRatio: false,
                responsive: true,
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
            },
            options: {
                maintainAspectRatio: false,
                responsive: true
            }
        }
    );

    setInterval(function () {
        $.ajax({
            url: base_url + 'chats_per_sec',
            type: 'GET',
            success: (data, textStatus, jqXHR) => {
                var series = liveChart.data.datasets[0].data;
                var latest_data_time = 0;
                if (series.length > 0) {
                    latest_data_time = series[series.length - 1]['x'];
                }

                $.each(data, function (idx, value) {
                    var a = value[1].split(/[^0-9]/);
                    var time = new Date(a[0], a[1] - 1, a[2], a[3], a[4], a[5]);
                    if (latest_data_time < time) {
                        series.push({
                            x: time,
                            y: value[0]
                        });
                        $('.chats-per-sec-span').text(value[0]);
                    }
                });
                liveChart.update();
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                alert("error : " + errorThrown)
            }
        });
    }, 1000);

    load_list();
});

function load_list() {
    $("#word-list").html('');
    $.ajax({
        url: base_url + 'word/rank/recent/20',
        type: 'GET',
        success: (data, textStatus, jqXHR) => {
            $.each(data, function (idx, value) {
                $('#word-list').append('<li class="word-list-item" name="' + value[0] + '">'
                    + '<div class="word-list-item-key-container">'
                    + '<span class="word-list-item-key">' + (idx + 1) + '</span>'
                    + '</div>'
                    + '<div class="word-list-item-value-container">'
                    + '<span class="word-list-item-value">' + value[0] + '</span>'
                    + '</div></li>');
            });

            $('.word-list-item').click(function () {
                load_chart($(this).attr('name'));
            });
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            alert("error : " + errorThrown)
        }
    });
}

function load_chart(word) {
    $.ajax({
        url: base_url + 'word/count/specify/' + word + "/10",
        type: 'GET',
        success: (data, textStatus, jqXHR) => {
            wordChart.data.datasets[0].data = data;
            wordChart.data.datasets[0].label = word;
            wordChart.update();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            alert("error : " + errorThrown)
        }
    });
}

