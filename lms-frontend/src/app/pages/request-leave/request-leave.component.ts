import { Component } from '@angular/core';
import { LeaveService } from '../../core/leave.service';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-request-leave',
  templateUrl: './request-leave.component.html'
})
export class RequestLeaveComponent {
  form = {
    type: 'SICK',   // MEDICAL | SICK | PRIVILEGED
    start: '',      // bound to date input (may be dd-MM-yyyy in your UI)
    end: '',
    reason: ''
  };

  submitting = false;
  errorMsg = '';
  successMsg = '';

  constructor(private ls: LeaveService) {}

  // Accept dd-MM-yyyy or yyyy-MM-dd, return ISO yyyy-MM-dd
  private toISO(d: string): string {
    const s = (d || '').trim();
    const ddmmyyyy = /^(\d{2})-(\d{2})-(\d{4})$/;   // e.g., 26-08-2025
    const yyyymmdd = /^(\d{4})-(\d{2})-(\d{2})$/;   // e.g., 2025-08-26
    if (ddmmyyyy.test(s)) {
      const [, dd, mm, yyyy] = s.match(ddmmyyyy)!;
      return `${yyyy}-${mm}-${dd}`;
    }
    if (yyyymmdd.test(s)) return s;
    // Last resort: let Date parse and build yyyy-MM-dd
    const x = new Date(s);
    if (isNaN(+x)) throw new Error('Invalid date');
    const yyyy = x.getFullYear();
    const mm = String(x.getMonth() + 1).padStart(2, '0');
    const dd = String(x.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }

  submit(): void {
    this.errorMsg = '';
    this.successMsg = '';

    let startISO = '', endISO = '';
    try {
      startISO = this.toISO(this.form.start);
      endISO = this.toISO(this.form.end);
    } catch {
      this.errorMsg = 'Please enter valid dates.';
      return;
    }

    const payload = {
      type: (this.form.type || '').toUpperCase().trim(),
      start_date: startISO,
      end_date: endISO,
      reason: (this.form.reason || '').trim() || undefined
    };

    this.submitting = true;
    this.ls.create(payload)
      .pipe(finalize(() => (this.submitting = false)))
      .subscribe({
        next: () => {
          this.successMsg = 'Leave request submitted successfully.';
        },
        error: (err) => {
          // Show precise, friendly errors
          let msg = err?.error?.message || 'Failed to submit leave request.';
          if (err?.status === 409) {
            msg = 'You already have a pending/approved leave overlapping these dates.';
          } else if (err?.status === 400 && err?.error) {
            const e = err.error;
            if (typeof e.remaining !== 'undefined' && typeof e.requested !== 'undefined') {
              msg = `Insufficient balance (${e.type}): Allowed ${e.allowed}, Taken ${e.taken}, Remaining ${e.remaining}, Requested ${e.requested}.`;
            }
          }
          this.errorMsg = msg;
        }
      });
  }
}
