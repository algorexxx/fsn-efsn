import React from 'react';
import {Button, Col, Container, Modal, ProgressBar, Row, Table,} from 'react-bootstrap'
import NumberFormat from 'react-number-format';
import Tooltip from '@material-ui/core/Tooltip';
import Delay from './Delay';
import axios from 'axios';
import Datamap from 'react-datamaps';
import ReactCountryFlag from "react-country-flag";
import TimeAgo from 'react-timeago';
import customStrings from './timeAgo/customStrings'
import buildFormatter from 'react-timeago/lib/formatters/buildFormatter'
import Spinner from './Spinner';
import AttentionWarning from './AttentionWarning';
import FusionLogo from '../img/Fusion_White.svg';
import loadApiPath, {loadPollingConfig} from '../config';
import startSnapshotPolling from '../snapshot-polling';

const statsApiPath = loadApiPath(process.env.REACT_APP_STATS_API_PATH);


const pollingConfig = loadPollingConfig(
    process.env.REACT_APP_STATS_POLL_INTERVAL_MS,
    process.env.REACT_APP_STATS_REQUEST_TIMEOUT_MS
);

class Main extends React.Component {
    state = {
        status: 'loading',
        observedAt: null,
        nodesList: [],
        geoCharts: [],
        totalNodes: null,
        activeNodes: null,
        highestBlock: null,
        lastUpdatedBlock: null,
        ticketNumber: null,
        pendingTransactions: null
    };

    componentDidMount() {
        this.polling = startSnapshotPolling(pollingConfig, {
            request: () => {
                const source = axios.CancelToken.source();
                return {
                    promise: axios.get(`${statsApiPath}/nodes`, {cancelToken: source.token}),
                    cancel: () => source.cancel()
                };
            },
            now: () => performance.now(),
            setTimeout: (callback, delay) => window.setTimeout(callback, delay),
            clearTimeout: timer => window.clearTimeout(timer),
            onSnapshot: snapshot => this.setState({...snapshot, status: 'ready'}),
            onUnavailable: () => this.setState({
                status: 'unavailable', nodesList: [], geoCharts: [], totalNodes: null,
                activeNodes: null, highestBlock: null, lastUpdatedBlock: null,
                ticketNumber: null, pendingTransactions: null, showModal: false
            })
        });
        document.addEventListener('visibilitychange', this.refreshVisiblePage);
    }

    refreshVisiblePage = () => {
        if (document.visibilityState === 'visible') {
            this.polling.refresh();
        }
    };

    componentWillUnmount() {
        document.removeEventListener('visibilitychange', this.refreshVisiblePage);
        this.polling.stop();
    }

    render() {

        let pinnedNodes = JSON.parse(localStorage.getItem('pinnedNodes')) === null ? [] : JSON.parse(localStorage.getItem('pinnedNodes'));
        const setPinnedNode = (nodename) => {
            let data = JSON.parse(localStorage.getItem('pinnedNodes'));
            let u = [];
            if (!Array.isArray(data)) {
                u.push(nodename);
                localStorage.setItem('pinnedNodes', JSON.stringify(u));
            } else {
                let data = JSON.parse(localStorage.getItem('pinnedNodes'));
                data.push(nodename);
                localStorage.setItem('pinnedNodes', JSON.stringify(data));
            }
            this.forceUpdate();
        }

        const removePinnedNode = (nodename) => {
            let data = JSON.parse(localStorage.getItem('pinnedNodes'));
            const filteredItems = data.filter(item => item !== nodename);
            localStorage.setItem('pinnedNodes', JSON.stringify(filteredItems));
            if (filteredItems.length === 0) {
                this.setState({
                    hideNonPinned: false
                })
            }

            this.forceUpdate();
        }

        const getVersionNumber = (string) => {
            const match = string.match(/(?:^|\/)v?([0-9]+\.[0-9]+\.[0-9]+)/);
            return match ? match[1] : string;
        }


        const blockClass = (nodeBlock, highestBlock, version) => {
            if (parseInt(version.substring(0, 1)) < 5) {
                return 'text-danger';
            } else if (highestBlock && nodeBlock) {
                if ((highestBlock - nodeBlock) === 1) {
                    return 'text-warn';
                } else if ((highestBlock - nodeBlock) > 1) {
                    return 'text-danger';
                }
            }
        }

        const latencyClass = (latency) => {
            if (latency > 100) {
                return 'text-warn'
            } else if (latency >= 1000) {
                return 'text-danger';
            }
        };

        const setShow = (state, id) => {
            return this.setState({
                showModal: state,
                showDetailsId: id
            });
        };

        const handleClose = () => setShow(false);
        const handleShow = () => setShow(true);

        const setNonPinned = (state) => {
            this.setState({
                hideNonPinned: state
            });
            this.forceUpdate();
        };

        const getTicketPercentage = (totalTickets, nodeTicket) => {
            if (totalTickets > 0 && nodeTicket !== null) {
                if (nodeTicket === 0) {
                    return '0% of all tickets';
                } else {
                    let o = totalTickets / 100;
                    return `${(nodeTicket / o).toFixed(2)}% of reported tickets`;
                }
            }
            return 'Ticket share unavailable';
        }

        const formatter = buildFormatter(customStrings);
        const missingValue = this.state.status === 'loading' ? <Spinner/> : '—';
        const formatHash = hash => `${hash.substring(0, 6)} … ${hash.substring(hash.length - 4)}`;

        return <div className={'bg-dark'}>
        <div className={'main-content'}>
            <Modal show={this.state.showModal} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>Geo Map</Modal.Title>
                </Modal.Header>
                {this.state.geoCharts && this.state.showModal ?
                    <Delay waitBeforeShow={200}>
                        <Datamap
                            fills={{
                                defaultFill: '#152e4d',
                                bubbleFill: '#ebebeb'
                            }}
                            responsive={true}
                            bubbles={this.state.geoCharts}
                        /> </Delay>
                    : missingValue}

                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
            <Container fluid={true}>
                <Row>
                    <Col md={12}>
                        <div className="row">
                            <div className="col-md-6">
                                <img src={FusionLogo} width="200px" className={'p-2'} alt=""/>
                            </div>
                        </div>
                    </Col>
                    <Col md={12}>
                        <div className="alert alert-primary mt-2">
                            <div className="row">
                                <div className="col-6">
                                        <span className={'text-white'}>
                                        Node reports do not establish chain agreement. Connection status does not prove that each report is recent.
                                        </span>
                                </div>
                                <div className="col-6 text-md-right">
                                    <a className="text-white" href="https://fusion.org">Learn more about FUSION <i
                                        className="fe fe-external-link mb-0"/></a>
                                </div>
                            </div>
                        </div>
                    </Col>
                    <Col md={12}>
                        <div role="status" aria-live="polite" className="alert alert-secondary mt-2">
                            {this.state.status === 'loading' && 'Loading dashboard…'}
                            {this.state.status === 'unavailable' && 'Dashboard data unavailable or expired. Retrying automatically.'}
                            {this.state.status === 'ready' && (this.state.totalNodes === 0 ? 'No nodes reported.' : 'Dashboard snapshot received.')}
                            {this.state.observedAt && <span> Last snapshot: <time dateTime={this.state.observedAt}>{this.state.observedAt}</time>.</span>}
                        </div>
                    </Col>
                    <Col md={2}>
                        <div className="card">
                            <div className="card-body">
                                <div className="row align-items-center">
                                    <div className="col">
                                        <h6 className="card-title text-uppercase text-muted mb-2">
                                            Highest Reported Block
                                        </h6>
                                        <span className="h2 mb-0">
                                                {this.state.highestBlock !== null ?
                                                    <NumberFormat value={this.state.highestBlock} displayType={'text'}
                                                                  thousandSeparator={true} prefix={"# "}/>
                                                    : missingValue}
                                            </span>
                                    </div>
                                    <div className="col-auto">
                                        <span className="h2 fe fe-box text-muted mb-0"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Col>
                    <Col md={2}>
                        <div className="card">
                            <div className="card-body">
                                <div className="row align-items-center">
                                    <div className="col">
                                        <h6 className="card-title text-uppercase text-muted mb-2">
                                            Block Report Received
                                        </h6>
                                        <span className="h2 mb-0">
                                                {this.state.lastUpdatedBlock ?
                                                    <TimeAgo date={this.state.lastUpdatedBlock}
                                                             formatter={formatter}/> : missingValue}
                                            </span>
                                    </div>
                                    <div className="col-auto">
                                        <span className="h2 fe fe-clock text-muted mb-0"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Col>
                    <Col md={2}>
                        <div className="card">
                            <div className="card-body">
                                <div className="row align-items-center">
                                    <div className="col">
                                        <h6 className="card-title text-uppercase text-muted mb-2">
                                            Average Block Time
                                        </h6>
                                        <span className="h2 mb-0">
                                                —
                                            </span>
                                    </div>
                                    <div className="col-auto text-center">
                                        <span className="h2 fe fe-briefcase text-muted mb-0"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Col>
                    <Col md={2}>
                        <div className="card">
                            <div className="card-body">
                                <div className="row align-items-center">
                                    <div className="col">
                                        <h6 className="card-title text-uppercase text-muted mb-2">
                                            Tickets
                                        </h6>
                                        <span className="h2 mb-0">
                                                {this.state.ticketNumber === null ? missingValue : this.state.ticketNumber}
                                            </span>
                                    </div>
                                    <div className="col-auto">
                                        <span className="h2 fe fe-credit-card text-muted mb-0"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Col>
                    <Col md={2}>
                        <div className="card">
                            <div className="card-body">
                                <div className="row align-items-center">
                                    <div className="col">
                                        <h6 className="card-title text-uppercase text-muted mb-2">
                                            Pending Txs
                                        </h6>
                                        <span className="h2 mb-0">
                                                {this.state.pendingTransactions === null ? missingValue : this.state.pendingTransactions}
                                            </span>
                                    </div>
                                    <div className="col-auto">
                                        <span className="h2 fe fe-clock text-muted mb-0"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Col>
                    <Col md={2}>
                        <div className="card">
                            <div className="card-body">
                                <div className="row align-items-center">
                                    <div className="col">
                                        <h6 className="card-title text-uppercase text-muted mb-2">
                                            Geo
                                        </h6>
                                        <button disabled={this.state.status !== 'ready' || this.state.geoCharts.length === 0} className={'btn btn-sm text-stats p-0'} onClick={() => {
                                            handleShow()
                                        }}>View Map
                                        </button>
                                    </div>
                                    <div className="col-auto">
                                        <span className="h2 fe fe-globe text-muted mb-0"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Col>
                </Row>
                <div className="col-md-12 pb-3 text-stats">
                    <div className="row">
                        <div className="mx-auto">
                            Connected Nodes {this.state.totalNodes !== null ?
                            <span
                                className={'nodes-badge p-1'}>{this.state.activeNodes}/{this.state.totalNodes}</span> : missingValue}
                        </div>
                        <div className="mx-auto">
                            {pinnedNodes.length > 0 ?
                                <span>Pinned Nodes</span> : ''} {pinnedNodes.length > 0 ?
                            <span
                                className={'nodes-badge p-1'}>{pinnedNodes.length}</span> : ''}
                        </div>
                        <div className="mx-auto">
                            {pinnedNodes.length > 0 ? <span className={'ml-3 overflow-auto'}>
                                Hide non-pinned Nodes {!this.state.hideNonPinned ?
                                <span className={'fe fe-square'} onClick={() => {
                                    setNonPinned(true)
                                }}></span> : <span className={'fe fe-x-square'} onClick={() => {
                                    setNonPinned(false)
                                }}></span>}
                            </span> : ''}
                        </div>
                        <div className="mx-auto">
                            Summary values come from the connected node reporting the highest block.
                        </div>
                    </div>
                </div>
                <div className={'col-md-12'}>
                    <div className={'table-responsive pt-3'}>
                        <Table className={'table table-sm table-nowrap card-table'} borderless variant="">
                            <thead className={'text-center text-muted'}>
                            <tr>
                                <th>Pin</th>
                                <th>Connected</th>
                                <Tooltip title="Location of the node">
                                    <th>Location</th>
                                </Tooltip>
                                <Tooltip title="Name of the node">
                                    <th>ID</th>
                                </Tooltip>
                                <Tooltip title="Current version of efsn">
                                    <th>Type</th>
                                </Tooltip>
                                <Tooltip title="The current block height the node is at">
                                    <th>Height</th>
                                </Tooltip>
                                <Tooltip title="When the collector received the reported block">
                                    <th>Block Received</th>
                                </Tooltip>
                                <Tooltip title="Pending Transactions in current block">
                                    <th>Pending Txs</th>
                                </Tooltip>
                                <Tooltip title="Amount of tickets the node owns">
                                    <th>Tickets</th>
                                </Tooltip>
                                <Tooltip title="Mining state">
                                    <th>Mining</th>
                                </Tooltip>
                                <Tooltip title="Syncing state">
                                    <th>Syncing</th>
                                </Tooltip>
                                <Tooltip title="Amount of peers">
                                    <th>Peers</th>
                                </Tooltip>
                                <th>Uptime</th>
                                <Tooltip title="Latency between stats server and the node">
                                    <th>Latency</th>
                                </Tooltip>
                            </tr>
                            </thead>
                            <tbody className={'text-center'}>
                            {
                                this.state.nodesList.map(((node, index) =>
                                        pinnedNodes.includes(this.state.nodesList[index].id) ?
                                            <tr key={node.id}>
                                                <td><a onClick={function () {
                                                    removePinnedNode(this.state.nodesList[index].id)
                                                }.bind(this)}>
                                                    <span className="fe fe-minus-square text-muted mb-0"></span>
                                                </a></td>
                                                <td>{this.state.nodesList[index].stats.active ?
                                                    <span className="text-success">●</span> :
                                                    <span className="text-danger">●</span>}</td>
                                                <td>{this.state.nodesList[index].geo ? <ReactCountryFlag cdnUrl={'/flags/4x3/'}
                                                    code={this.state.nodesList[index].geo.country.toLowerCase()}
                                                    svg/> : '?'}</td>
                                                <td>{this.state.nodesList[index].id}</td>
                                                <td>
                                                    <Tooltip title={this.state.nodesList[index].info.node}>
                                                        <span>{getVersionNumber(this.state.nodesList[index].info.node)}</span>
                                                    </Tooltip>
                                                </td>
                                                <td className={blockClass(this.state.nodesList[index].stats.block.number, this.state.highestBlock, getVersionNumber(this.state.nodesList[index].info.node))}>

                                                    {<NumberFormat
                                                            value={this.state.nodesList[index].stats.block.number}
                                                            displayType={'text'} thousandSeparator={true}
                                                            prefix={"# "}/>}
                                                    <span
                                                        className={'pl-4'}>{formatHash(this.state.nodesList[index].stats.block.hash)}
                                                        <AttentionWarning
                                                            highestBlock={this.state.highestBlock || 0}
                                                            currentBlock={this.state.nodesList[index].stats.block.number}
                                                            version={getVersionNumber(this.state.nodesList[index].info.node)}/>
                                                                      </span>
                                                </td>
                                                <td>{this.state.nodesList[index].stats.block.received ?
                                                    <TimeAgo
                                                        date={this.state.nodesList[index].stats.block.received}
                                                        formatter={formatter}/> : '—'}</td>
                                                <td>{this.state.nodesList[index].stats.pending}</td>
                                                <Tooltip
                                                    title={getTicketPercentage(this.state.ticketNumber, this.state.nodesList[index].stats.myTicketNumber)}>
                                                    <td>{this.state.nodesList[index].stats.myTicketNumber}</td>
                                                </Tooltip>
                                                <td>{this.state.nodesList[index].stats.mining ?
                                                    <span className="text-success">●</span> :
                                                    <span className="text-danger">●</span>}</td>
                                                <td>{this.state.nodesList[index].stats.syncing ?
                                                    <span className="text-success">●</span> :
                                                    <span className="text-danger">●</span>}</td>
                                                <td>{this.state.nodesList[index].stats.peers}</td>
                                                <td><ProgressBar now={this.state.nodesList[index].stats.uptime}
                                                                 label={`${this.state.nodesList[index].stats.uptime}%`}/>
                                                </td>
                                                <td className={latencyClass(this.state.nodesList[index].stats.latency)}>{this.state.nodesList[index].stats.latency}ms</td>
                                            </tr>
                                            : null
                                ))
                            }
                            {
                                this.state.nodesList.map(((node, index) =>
                                        !pinnedNodes.includes(this.state.nodesList[index].id) && !this.state.hideNonPinned ?
                                            <tr key={node.id}>
                                                <td><a onClick={function () {
                                                    setPinnedNode(this.state.nodesList[index].id)
                                                }.bind(this)}>
                                                    <span className="fe fe-square text-muted mb-0"></span>
                                                </a></td>
                                                <td>{this.state.nodesList[index].stats.active ?
                                                    <span className="text-success">●</span> :
                                                    <span className="text-danger">●</span>}</td>
                                                <td>{this.state.nodesList[index].geo ? <ReactCountryFlag cdnUrl={'/flags/4x3/'}
                                                    code={this.state.nodesList[index].geo.country.toLowerCase()}
                                                    svg/> : '?'}</td>
                                                <td>{this.state.nodesList[index].id}</td>
                                                <td>
                                                    <Tooltip title={this.state.nodesList[index].info.node}>
                                                        <span>{getVersionNumber(this.state.nodesList[index].info.node)}</span>
                                                    </Tooltip>
                                                </td>
                                                <td className={blockClass(this.state.nodesList[index].stats.block.number, this.state.highestBlock, getVersionNumber(this.state.nodesList[index].info.node))}>

                                                    {<NumberFormat
                                                            value={this.state.nodesList[index].stats.block.number}
                                                            displayType={'text'} thousandSeparator={true}
                                                            prefix={"# "}/>}
                                                    <span
                                                        className={'pl-4'}>{formatHash(this.state.nodesList[index].stats.block.hash)}
                                                        <AttentionWarning
                                                            highestBlock={this.state.highestBlock || 0}
                                                            currentBlock={this.state.nodesList[index].stats.block.number}
                                                            version={getVersionNumber(this.state.nodesList[index].info.node)}/>
                                                                      </span>
                                                </td>
                                                <td>{this.state.nodesList[index].stats.block.received ?
                                                    <TimeAgo
                                                        date={this.state.nodesList[index].stats.block.received}
                                                        formatter={formatter}/> : '—'}</td>
                                                <td>{this.state.nodesList[index].stats.pending}</td>
                                                <Tooltip
                                                    title={getTicketPercentage(this.state.ticketNumber, this.state.nodesList[index].stats.myTicketNumber)}>
                                                    <td>{this.state.nodesList[index].stats.myTicketNumber}</td>
                                                </Tooltip>
                                                <td>{this.state.nodesList[index].stats.mining ?
                                                    <span className="text-success">●</span> :
                                                    <span className="text-danger">●</span>}</td>
                                                <td>{this.state.nodesList[index].stats.syncing ?
                                                    <span className="text-success">●</span> :
                                                    <span className="text-danger">●</span>}</td>
                                                <td>{this.state.nodesList[index].stats.peers}</td>
                                                <td><ProgressBar now={this.state.nodesList[index].stats.uptime}
                                                                 label={`${this.state.nodesList[index].stats.uptime}%`}/>
                                                </td>
                                                <td className={latencyClass(this.state.nodesList[index].stats.latency)}>{this.state.nodesList[index].stats.latency}ms</td>
                                            </tr>
                                            : null
                                ))
                            }
                            </tbody>
                        </Table>
                    </div>
                </div>
            </Container>
        </div>
        </div>;
    }
}

export default Main;
