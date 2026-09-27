import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import ViewBoundary from './ViewBoundary';

it('withholds raw errors, preserves surrounding navigation and recovers only on request', async()=>{
  const log=vi.spyOn(console,'error').mockImplementation(()=>{});
  let fail=true;
  function Content() { if(fail) throw new Error('private-provider-payload'); return <p>Research restored</p>; }
  try {
    render(<><nav>Workspace navigation</nav><ViewBoundary><Content /></ViewBoundary></>);
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByRole('navigation')).toBeTruthy();
    expect(screen.queryByText('private-provider-payload')).toBeNull();
    fail=false;
    expect(screen.queryByText('Research restored')).toBeNull();
    await userEvent.click(screen.getByRole('button',{name:'Retry display'}));
    expect(screen.getByText('Research restored')).toBeTruthy();
  } finally { log.mockRestore(); }
});
