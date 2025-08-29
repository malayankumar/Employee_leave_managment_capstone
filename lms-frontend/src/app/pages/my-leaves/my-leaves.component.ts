import { Component, OnInit } from '@angular/core';
import { LeaveService } from '../../core/leave.service';
@Component({ selector: 'app-my-leaves', templateUrl: './my-leaves.component.html' })
export class MyLeavesComponent implements OnInit {
  rows:any[]=[];
  balance: any | null = null;
  year = new Date().getFullYear();
  constructor(private ls: LeaveService){}
  ngOnInit(){
    this.ls.myLeaves().subscribe(r=> this.rows=r);
    this.loadBalance();
    }
  loadBalance(){
    this.ls.getMyBalance(this.year).subscribe(res => this.balance = res);
  }
}
