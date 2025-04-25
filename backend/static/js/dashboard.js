document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const callNextBtn = document.getElementById('call-next');
    const resetQueueBtn = document.getElementById('reset-queue');
    const currentlyCalledEl = document.getElementById('currently-called');
    const waitingTicketsEl = document.getElementById('waiting-tickets');
    const totalIssuedEl = document.getElementById('total-issued');
    const highestTicketEl = document.getElementById('highest-ticket');
    const ticketHistoryEl = document.getElementById('ticket-history');

    // Add highlight effect to show updates
    function highlightElement(element) {
        element.classList.remove('highlight');
        // Trigger reflow
        void element.offsetWidth;
        element.classList.add('highlight');
    }

    // Format datetime for display
    function formatDateTime(isoString) {
        const date = new Date(isoString);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }

    // Update queue status
    async function updateQueueStatus() {
        try {
            const response = await fetch('/queue_status');
            const data = await response.json();

            waitingTicketsEl.textContent = data.waiting_tickets;
            totalIssuedEl.textContent = data.total_issued;
            highestTicketEl.textContent = data.highest_ticket;

            highlightElement(waitingTicketsEl.parentElement);
        } catch (error) {
            console.error('Error updating queue status:', error);
        }
    }

    // Update currently called ticket
    async function updateCurrentlyCalled() {
        try {
            const response = await fetch('/currently_called');
            const data = await response.json();

            if (data.currently_called) {
                currentlyCalledEl.innerHTML = `<div class="ticket-number">${data.currently_called}</div>`;
            } else {
                currentlyCalledEl.innerHTML = `<div class="no-ticket">No ticket called yet</div>`;
            }

            highlightElement(currentlyCalledEl);
        } catch (error) {
            console.error('Error updating currently called:', error);
        }
    }

    // Update ticket history
    async function updateTicketHistory() {
        try {
            const response = await fetch('/ticket_history?limit=5');
            const data = await response.json();

            if (data.length > 0) {
                let html = '<ul>';
                data.forEach(ticket => {
                    html += `
                        <li>
                            <span class="ticket-number">${ticket.ticket_number}</span>
                            <span class="ticket-time">${formatDateTime(ticket.called_at)}</span>
                        </li>
                    `;
                });
                html += '</ul>';
                ticketHistoryEl.innerHTML = html;
            } else {
                ticketHistoryEl.innerHTML = `<p class="no-history">No tickets have been called yet</p>`;
            }

            highlightElement(ticketHistoryEl);
        } catch (error) {
            console.error('Error updating ticket history:', error);
        }
    }

    // Call next ticket
    async function callNext() {
        try {
            callNextBtn.disabled = true;

            const response = await fetch('/call_next', {
                method: 'POST'
            });

            if (response.ok) {
                await updateCurrentlyCalled();
                await updateQueueStatus();
                await updateTicketHistory();
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail}`);
            }

            callNextBtn.disabled = false;
        } catch (error) {
            console.error('Error calling next ticket:', error);
            callNextBtn.disabled = false;
        }
    }

    // Reset queue
    async function resetQueue() {
        if (!confirm('Are you sure you want to reset the queue? This will mark all tickets as attended.')) {
            return;
        }

        try {
            resetQueueBtn.disabled = true;

            const response = await fetch('/reset_queue', {
                method: 'POST'
            });

            if (response.ok) {
                await updateQueueStatus();
                alert('Queue has been reset successfully.');
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail}`);
            }

            resetQueueBtn.disabled = false;
        } catch (error) {
            console.error('Error resetting queue:', error);
            resetQueueBtn.disabled = false;
        }
    }

    // Add event listeners
    callNextBtn.addEventListener('click', callNext);
    resetQueueBtn.addEventListener('click', resetQueue);

    // Initial data load
    updateQueueStatus();
    updateCurrentlyCalled();
    updateTicketHistory();

    // Set up auto-refresh
    setInterval(updateQueueStatus, 5000);  // Refresh every 5 seconds
    setInterval(updateCurrentlyCalled, 5000);
    setInterval(updateTicketHistory, 5000);
});