import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import ResearchAllowance from './ResearchAllowance';
import { setLocale } from './i18n';

it('labels cooperative allowance in both languages without promising a cost cap',async()=>{
  setLocale('en');const change=vi.fn();
  render(<ResearchAllowance seconds={1800} onChange={change} disabled={false}/>);
  expect(screen.getByText(/does not guarantee a report or cap AI charges/)).toBeTruthy();
  await userEvent.selectOptions(screen.getByRole('combobox'),'3600');expect(change).toHaveBeenCalledWith(3600);
  act(()=>setLocale('vi'));
  expect(screen.getByText(/không phải giới hạn chi phí AI/)).toBeTruthy();
  expect(screen.getByRole('combobox',{name:'Thời lượng cho nghiên cứu'})).toBeTruthy();
  act(()=>setLocale('en'));
});
it('cannot change allowance while work or submission is pending',()=>{
  setLocale('en');render(<ResearchAllowance seconds={1800} onChange={vi.fn()} disabled/>);
  expect((screen.getByRole('combobox') as HTMLSelectElement).disabled).toBe(true);
});
