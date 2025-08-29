import { Component, OnInit } from '@angular/core';
import { LeaveService } from '../../core/leave.service';
import { finalize } from 'rxjs/operators';

@Component({ selector: 'app-approvals', templateUrl: './approvals.component.html' })
export class ApprovalsComponent implements OnInit {
  rows: any[] = [];
  loading = false;
  acting = new Set<number>();  // prevent double-click spam

  // balances
  showBalances = false;
  balancesLoading = false;
  balances: any[] = [];
  year = new Date().getFullYear();

  constructor(private ls: LeaveService) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.loading = true;
    this.ls.pending()
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: r => (this.rows = r || []),
        error: err => {
          console.error(err);
          alert(err?.error?.message || 'Failed to load pending approvals.');
        },
      });
  }

  approve(id: number, remark?: string): void {
    if (this.acting.has(id)) return;
    const finalRemark = (remark ?? '').trim();
    this.acting.add(id);
    this.ls.approve(id, finalRemark)
      .pipe(finalize(() => this.acting.delete(id)))
      .subscribe({
        next: () => {
          this.refresh();
          if (this.showBalances) this.loadBalances();
        },
        error: err => {
          console.error(err);
          alert(err?.error?.message || 'Failed to approve. Please try again.');
        },
      });
  }

  reject(id: number, remark?: string): void {
    if (this.acting.has(id)) return;
    const finalRemark = (remark ?? '').trim();
    this.acting.add(id);
    this.ls.reject(id, finalRemark)
      .pipe(finalize(() => this.acting.delete(id)))
      .subscribe({
        next: () => {
          this.refresh();
          if (this.showBalances) this.loadBalances();
        },
        error: err => {
          console.error(err);
          alert(err?.error?.message || 'Failed to reject. Please try again.');
        },
      });
  }

  toggleBalances(): void {
    this.showBalances = !this.showBalances;
    if (this.showBalances) this.loadBalances();
  }

  loadBalances(): void {
    this.balancesLoading = true;
    this.ls.getAllBalances(this.year)
      .pipe(finalize(() => (this.balancesLoading = false)))
      .subscribe({
        next: r => (this.balances = r || []),
        error: err => {
            console.error(err);
            alert(err?.error?.message || 'Failed to load balances.');
        },
      });
  }

  onYearChange(): void {
    if (this.showBalances) this.loadBalances();
  }
}
