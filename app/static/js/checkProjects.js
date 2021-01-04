$(function() {
    $('#projectSelect').change(function () {
        let jqxhr = $.getJSON('/api/projects/available', {
            projectName: this.value
        })
            .done(function (data) {
                switch (data.status) {
                    case 'error':
                        $('#projectSelect').addClass('is-invalid');
                        $('#teamSelectDiv').empty();
                        $('#teamSelectDiv').append(`<p class="lead">${data.message}</p>`);
                        break;
                    case 'success':
                        $('#projectSelect').removeClass('is-invalid').addClass('is-valid');
                        $('#teamSelectDiv').empty();

                        $.get('/static/team_select.html', function (html) {
                           $('#teamSelectDiv').append(html);
                        });

                        data.data.teams.forEach(function (team) {
                            let teamName = team.name;
                            if (!teamName)
                                teamName = '(без названия) ';

                            $('#teamSelect').append(`<option>${teamName} (свободных мест: ${team.emptySlots})</option>`);
                        });
                        break;
                }
            })
            .fail(function (data) {
                console.error(data);
            });
    });
});