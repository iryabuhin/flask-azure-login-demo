$(function() {
    $('.selectpicker').selectpicker();

    let originalDropdownSelectBackgroundColor = $('.bootstrap-select > .dropdown-toggle').css('background-color');

    $(document).on('change', '#projectSelect', function () {
        let selectedProjectId = $(this).find(':selected').data('documentId');
        let cardFooter = $('.card-footer');
        let projectSelectButton = $('.bootstrap-select > .dropdown-toggle');
        let teamSelectDiv = $(document).find('#teamSelectDiv');

        $.getJSON(`/api/projects/${selectedProjectId}/available`, {})
            .done(function (response) {
                switch (response.status) {
                    case 'error':
                        projectSelectButton.removeClass('border-gray').addClass('border-danger').addClass('border-4');

                        teamSelectDiv.empty();
                        teamSelectDiv.prop('hidden', true);
                        cardFooter.empty();
                        cardFooter.append(`<p class="lead text-dark">${response.message}</p>`);
                        break;
                    case 'success':
                        projectSelectButton.removeClass('border-danger').addClass('border-gray');

                        teamSelectDiv.empty();
                        teamSelectDiv.prop('hidden', false);
                        teamSelectDiv.html(
                            '<label for="#teamSelect">Команда</label>' +
                            '<select id="teamSelect" class="selectpicker show-tick" title="Выберите команду" data-width="100%" data-style="border border-grey" ></select>'
                        );

                        let teams = response.data.teams;

                        teams.filter(team => !team.isFull).forEach(function (team) {
                            $('#teamSelect').append(`<option>${team.name} (свободных мест: ${team.emptySlots.toString()})</option>`);
                        });

                        $('.selectpicker').selectpicker('refresh');

                        cardFooter.empty()
                        cardFooter.html('<button type="submit" id="submit" class="btn btn-lg btn-primary" disabled>Записаться</button>');

                        break;
                }
            })
            .fail(function (data) {
                console.error(data);
            });
    });

    $(document).on('change', '#teamSelect', function () {
        if ($(this).val() !== '') {
            $(document).find('#submit').removeAttr('disabled');
        }
    });

    $(document).on('click', '#submit', function (event) {
        event.preventDefault();

        if (!$(document).find('#teamSelect') || $('#teamSelect').val() === '') {
            $(this);
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
                    window.location = `/success?team_number=${data.teamNumber}&cell_index=${data.cellIndex}&project_name=${data.projectName}`
                    break;
                case 'error':
                    let submitButton = $(document).find('#submit');
                    let cardFooter = $('.card-footer');
                    submitButton.remove('span');
                    submitButton.text('Записаться')
                    submitButton.removeClass('btn-success').addClass('btn-danger');

                    cardFooter.text(response.message);
                    cardFooter.addClass('text-danger').addClass('font-weight-bold');

                    break;
            }

        }).fail(function (resp) {
            let submitButton = $(document).find('#submit');
            submitButton.attr('disabled', true);
            submitButton.text('Ошибка');
            submitButton.removeClass('btn-success').addClass('btn-danger');

            let text = '';
            if (resp.message) {
                text = resp.message;
            }
            else {
                text = 'Произошла внутренняя ошибка сервера';
            }

            $('.card-footer').addClass('text-danger').addClass('font-weight-bold');
            $('.card-footer').text(text);
        });
    });
});