from pathlib import Path

bundle = Path(__file__).resolve().parent
file = bundle.parents[2] / 'tmp/fsn-stats-auth/react-frontend/src/Components/Main.js'
source = file.read_bytes()
newline = '\r\n' if b'\r\n' in source else '\n'
value = source.decode('utf-8').replace('\r\n', '\n')
value = value.replace("import startSnapshotPolling from '../snapshot-polling';", "import startSnapshotPolling from '../snapshot-polling';\nimport {readPinnedNodes, writePinnedNodes} from '../pinned-nodes';", 1)
value = value.replace("        status: 'loading',", "        status: 'loading',\n        pinnedNodes: readPinnedNodes(),\n        pinStorageFailed: false,\n        hideNonPinned: false,", 1)
start = value.index("        let pinnedNodes = JSON.parse(localStorage.getItem('pinnedNodes'))")
end = value.index('        const getVersionNumber', start)
value = value[:start] + '''        const pinnedNodes = this.state.pinnedNodes;
        const setPinnedNode = id => this.updatePinnedNodes([...pinnedNodes, id]);
        const removePinnedNode = id => this.updatePinnedNodes(pinnedNodes.filter(pinned => pinned !== id));

''' + value[end:]
marker = '    render() {\n'
assert value.count(marker) == 1
value = value.replace(marker, '''    updatePinnedNodes = pinnedNodes => {
        const saved = writePinnedNodes(pinnedNodes);
        this.setState({
            pinnedNodes,
            pinStorageFailed: !saved,
            hideNonPinned: pinnedNodes.length > 0 && this.state.hideNonPinned
        });
    };

''' + marker, 1)
marker = "                <div className={'col-md-12'}>\n                    <div className={'table-responsive pt-3'}>"
assert value.count(marker) == 1
value = value.replace(marker, '''                {this.state.pinStorageFailed ? <p role="status" className="col-md-12 text-stats">
                    Pin changes cannot be saved in this browser. They will last until this page is reloaded.
                </p> : null}
''' + marker, 1)
file.write_bytes(value.replace('\n', newline).encode('utf-8'))
