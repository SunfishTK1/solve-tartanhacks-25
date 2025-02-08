import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { TreeNode } from '../tree-processing/tree-node.interface';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SummaryService {
  private apiUrl = 'https://18.191.231.140';

  constructor(private http: HttpClient) {}

  fetchSummary(sessionId: string): Observable<{content: string}> {
    return this.http.get<{content: string}>(`${this.apiUrl}/get_summary?session_id=${sessionId}`);
  }
} 