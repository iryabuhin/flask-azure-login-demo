$(function() {
    $('.selectpicker').selectpicker();

    let originalDropdownSelectBackgroundColor = $('.bootstrap-select > .dropdown-toggle').css('background-color');

    $(document).on('change', '#projectSelect', function () {
        let selectedProjectId = $(this).find(':selected').data('documentId');
        let cardFooter = $('.card-footer');
        let dropdownToggleButton = $('.bootstrap-select > .dropdown-toggle');

        $.getJSON(`/api/projects/${selectedProjectId}/available`, {})
            .done(function (response) {
                switch (response.status) {
                    case 'error':
                        dropdownToggleButton.css('background-color', '#d9534f');

                        cardFooter.empty();
                        cardFooter.append(`<p class="lead text-danger font-weight-bold">${response.message}</p>`);
                        break;
                    case 'success':
                        dropdownToggleButton.css('background-color', originalDropdownSelectBackgroundColor);
                        $('form').append('<div class="row justify-content-center" id="teamSelectDiv"></div>')
                        let teamSelectDiv = $('#teamSelectDiv');

                        teamSelectDiv.empty();
                        teamSelectDiv.append('<select title="Выберите команду" data-width="500px" data-style="btn-primary" id="teamSelect" class="selectpicker show-tick"></select>');

                        let teams = response.data.teams;

                        teams.filter(team => !team.isFull).forEach(function (team) {
                            $('#teamSelect').append(`<option>${team.name} (свободных мест: ${team.emptySlots.toString()})</option>`);
                        });

                        $('.selectpicker').selectpicker();
                        // let cardFooter = $('.card-footer');
                        cardFooter.empty()
                        cardFooter.append('<button type="submit" id="submit" class="btn btn-lg btn-success">Записаться</button>');

                        break;
                }
            })
            .fail(function (data) {
                console.error(data);
            });
    });

    $(document).on('click', '#submit', function (event) {
        event.preventDefault();

        if (!$(document).find('#teamSelect') || $('#teamSelect').val() === 'default') {
            return;
        }

        $(this).prop('disabled', true);
        $(this).html(
            '<span class="spinner-border spinner-border mr-1" role="status" aria-hidden="true"></span>'
        );

        let selectedProjectDocumentId = $('#projectSelect').find(':selected').data('documentId');
        let data = {
            name: $('#fullName').text(),
            group: $('#group').text(),
            team: $('#teamSelect').val()
        };

        $.ajax(`/api/projects/${selectedProjectDocumentId }/join`, {
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data)
        }).done(function (response) {
            let data = response.data;
            switch (response.status) {
                case 'success':
                    $.ajax('/success')
                    window.location = `/success?team_number=${data.teamNumber}&cell_index=${data.cellIndex}&project_name=${data.projectName}`
                    break;
                case 'error':
                    let submitButton = $(document).find('#submit');
                    let cardFooter = $('.card-footer');
                    submitButton.remove('span');
                    submitButton.text('Записаться')
                    submitButton.removeClass('btn-success').addClass('btn-danger');

                    cardFooter.text(response.message)

            }

        }).fail(function (resp) {
            console.error(resp);
            let submitButton = $(document).find('#submit');
            submitButton.attr('disabled', true);
            submitButton.text('Ошибка');
            $('.card-footer').text(resp.message).addClass('text-danger lead');
        });
    });
});